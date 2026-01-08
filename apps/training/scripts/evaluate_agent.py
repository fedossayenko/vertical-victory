#!/usr/bin/env python3
"""
evaluate_agent.py - Evaluate trained PPO agent

Evaluates a trained model against various opponents and generates metrics.
"""

import os
import sys
import argparse
from typing import Dict, List
from pathlib import Path

import numpy as np
import gymnasium as gym
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor

# Import MaskablePPO evaluation utilities
from sb3_contrib.common.maskable.evaluation import evaluate_policy

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from five_towers.env import FiveTowersEnv
from five_towers.game_logic.scoring import calculate_player_score


def load_model(model_path: str, env):
    """Load trained model from path."""
    # Import here to avoid loading if not needed
    from sb3_contrib import MaskablePPO

    return MaskablePPO.load(model_path, env=env)


def load_vec_normalize(stats_path: str, env):
    """Load VecNormalize statistics."""
    if os.path.exists(stats_path):
        stats = VecNormalize.load(stats_path, env)
        print(f"✓ Loaded VecNormalize statistics from {stats_path}")
        return stats
    return None


def create_eval_env(num_players: int = 2, seed: int = 0):
    """Create evaluation environment."""
    from sb3_contrib.common.wrappers import ActionMasker

    def mask_fn(env):
        return env.action_masks()

    def make_env():
        env = FiveTowersEnv(num_players=num_players)
        env.reset(seed=seed)
        env = ActionMasker(env, mask_fn)
        env = Monitor(env)
        return env

    return make_env


def evaluate_agent(
    model_path: str,
    stats_path: str,
    num_episodes: int = 100,
    num_players: int = 2,
    seed: int = 0,
):
    """
    Evaluate trained agent.

    Args:
        model_path: Path to trained model
        stats_path: Path to VecNormalize statistics
        num_episodes: Number of evaluation episodes
        num_players: Number of players
        seed: Random seed
    """
    print("=" * 60)
    print("Five Towers Agent Evaluation")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Episodes: {num_episodes}")
    print(f"Players: {num_players}")
    print("=" * 60)

    # Create environment
    print("\n[1/4] Creating evaluation environment...")
    env = create_eval_env(num_players=num_players, seed=seed)
    env = DummyVecEnv([env])

    # Load VecNormalize stats if available
    if stats_path and os.path.exists(stats_path):
        env = load_vec_normalize(stats_path, env)

    # Load model
    print("\n[2/4] Loading model...")
    model = load_model(model_path, env)
    print(f"✓ Model loaded from {model_path}")

    # Evaluate using sb3-contrib's evaluate_policy
    print("\n[3/4] Running evaluation...")
    mean_reward, std_reward = evaluate_policy(
        model,
        env,
        n_eval_episodes=num_episodes,
        deterministic=True,
    )

    print(f"\nResults:")
    print(f"  Mean reward: {mean_reward:.3f} +/- {std_reward:.3f}")

    # Detailed statistics
    print("\n[4/4] Collecting detailed statistics...")

    stats = collect_statistics(model, env, num_episodes)

    print("\n" + "=" * 60)
    print("Detailed Statistics")
    print("=" * 60)

    print(f"\nGame Outcomes:")
    print(f"  Wins: {stats['wins']} ({stats['win_rate']:.1f}%)")
    print(f"  Losses: {stats['losses']} ({stats['loss_rate']:.1f}%)")
    print(f"  Draws: {stats['draws']} ({stats['draw_rate']:.1f}%)")

    print(f"\nScoring:")
    print(f"  Agent avg score: {stats['agent_mean_score']:.2f}")
    print(f"  Opponent avg score: {stats['opponent_mean_score']:.2f}")
    print(f"  Avg score margin: {stats['avg_score_margin']:.2f}")

    print(f"\nGame Length:")
    print(f"  Avg rounds: {stats['avg_rounds']:.1f}")
    print(f"  Min rounds: {stats['min_rounds']}")
    print(f"  Max rounds: {stats['max_rounds']}")

    # Performance categories
    print("\n" + "=" * 60)
    print("Performance Assessment")
    print("=" * 60)

    if stats['win_rate'] >= 70:
        print("  ✓ EXCELLENT: Strong performance")
    elif stats['win_rate'] >= 55:
        print("  ✓ GOOD: Above random baseline")
    elif stats['win_rate'] >= 45:
        print("  ~ MODERATE: Near random baseline")
    else:
        print("  ✗ POOR: Below random baseline")

    # Close environment
    env.close()

    return stats


def collect_statistics(model, env, num_episodes: int) -> Dict:
    """
    Collect detailed statistics from model evaluation.

    Args:
        model: Trained model
        env: Evaluation environment
        num_episodes: Number of episodes to run

    Returns:
        Dictionary with statistics
    """
    wins = 0
    losses = 0
    draws = 0

    agent_scores = []
    opponent_scores = []
    score_margins = []

    round_counts = []

    for episode in range(num_episodes):
        obs = env.reset()
        done = False

        episode_data = []

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            step_result = env.step(action)
            if len(step_result) == 4:
                obs, reward, done, info = step_result
                truncated = False
            else:
                obs, reward, done, truncated, info = step_result

            done_flag = done or truncated

            # Extract episode info if available
            if isinstance(info, dict):
                if 'episode' in info:
                    episode_data.append(info['episode'])

        # Progress output every 10 episodes
        if (episode + 1) % 10 == 0:
            print(f"  Processed {episode + 1}/{num_episodes} episodes...", flush=True)

        # Get final scores (need to access underlying env)
        unwrapped_env = env.get_attr('game_state')[0] if hasattr(env, 'get_attr') else None

        if unwrapped_env:
            agent_score = calculate_player_score(unwrapped_env.players[0])
            opponent_score = calculate_player_score(unwrapped_env.players[1])

            agent_scores.append(agent_score)
            opponent_scores.append(opponent_score)
            score_margins.append(agent_score - opponent_score)

            if agent_score > opponent_score:
                wins += 1
            elif agent_score < opponent_score:
                losses += 1
            else:
                draws += 1

            round_counts.append(unwrapped_env.round_number)

    return {
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'win_rate': wins / num_episodes * 100,
        'loss_rate': losses / num_episodes * 100,
        'draw_rate': draws / num_episodes * 100,
        'agent_mean_score': np.mean(agent_scores) if agent_scores else 0,
        'opponent_mean_score': np.mean(opponent_scores) if opponent_scores else 0,
        'avg_score_margin': np.mean(score_margins) if score_margins else 0,
        'avg_rounds': np.mean(round_counts) if round_counts else 0,
        'min_rounds': min(round_counts) if round_counts else 0,
        'max_rounds': max(round_counts) if round_counts else 0,
    }


def compare_models(
    model_paths: List[str],
    stats_path: str,
    num_episodes: int = 100,
    num_players: int = 2,
    seed: int = 0,
):
    """
    Compare multiple models side-by-side.

    Args:
        model_paths: List of model paths to compare
        stats_path: Path to VecNormalize statistics
        num_episodes: Number of evaluation episodes
        num_players: Number of players
        seed: Random seed
    """
    print("=" * 60)
    print("Model Comparison")
    print("=" * 60)
    print(f"Comparing {len(model_paths)} models")
    print("=" * 60)

    results = []

    for model_path in model_paths:
        print(f"\nEvaluating: {model_path}")
        stats = evaluate_agent(
            model_path=model_path,
            stats_path=stats_path,
            num_episodes=num_episodes,
            num_players=num_players,
            seed=seed,
        )
        results.append((model_path, stats))

    # Summary table
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"{'Model':<40} {'Win Rate':<12} {'Avg Score':<12}")
    print("-" * 60)

    for model_path, stats in results:
        model_name = os.path.basename(model_path)
        print(f"{model_name:<40} {stats['win_rate']:>10.1f}%   {stats['agent_mean_score']:>10.2f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Evaluate trained PPO agent for Five Towers',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'model',
        type=str,
        nargs='+',
        help='Path to trained model(s)'
    )
    parser.add_argument(
        '--stats', '-s',
        type=str,
        default='vec_normalize.pkl',
        help='Path to VecNormalize statistics'
    )
    parser.add_argument(
        '--episodes', '-e',
        type=int,
        default=100,
        help='Number of evaluation episodes'
    )
    parser.add_argument(
        '--players', '-p',
        type=int,
        default=2,
        choices=[2, 3, 4, 5],
        help='Number of players'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=0,
        help='Random seed'
    )

    args = parser.parse_args()

    # If multiple models, compare them
    if len(args.model) > 1:
        compare_models(
            model_paths=args.model,
            stats_path=args.stats,
            num_episodes=args.episodes,
            num_players=args.players,
            seed=args.seed,
        )
    else:
        evaluate_agent(
            model_path=args.model[0],
            stats_path=args.stats,
            num_episodes=args.episodes,
            num_players=args.players,
            seed=args.seed,
        )


if __name__ == '__main__':
    main()
