#!/usr/bin/env python3
"""
train_ppo.py - PPO Training for Five Towers with Action Masking

Based on 2024-2025 best practices from Stable-Baselines3 and sb3-contrib.
Uses MaskablePPO for efficient action masking in card games.
"""

import os
import time
import argparse
from typing import Callable, Optional
from pathlib import Path

import numpy as np
import gymnasium as gym
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_checker import check_env

# Import MaskablePPO from sb3-contrib
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
from sb3_contrib.common.maskable.evaluation import evaluate_policy

# Import custom environment
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from five_towers.env import FiveTowersEnv
from five_towers.utils.rewards import RewardShaper, create_reward_shaper


def mask_fn(env: gym.Env) -> np.ndarray:
    """
    Return action mask for invalid action masking.

    This function is called by ActionMasker to get the mask.

    Args:
        env: Gym environment (unwrapped)

    Returns:
        Boolean mask: True = valid action, False = invalid action
    """
    return env.action_masks()


def make_env(
    seed: int = 0,
    rank: int = 0,
    eval_env: bool = False,
    num_players: int = 2,
    render_mode: Optional[str] = None,
):
    """
    Create a training environment.

    Args:
        seed: Random seed
        rank: Environment rank (for parallel environments)
        eval_env: Whether this is an evaluation environment
        num_players: Number of players in the game
        render_mode: Rendering mode

    Returns:
        Callable that creates the environment
    """
    def _init():
        env = FiveTowersEnv(
            num_players=num_players,
            render_mode=render_mode,
        )
        env.reset(seed=seed + rank)

        # Wrap with ActionMasker for MaskablePPO compatibility
        env = ActionMasker(env, mask_fn)

        return env

    return _init


def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """
    Linear learning rate schedule.

    Args:
        initial_value: Initial learning rate

    Returns:
        Schedule function
    """
    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value

    return func


def train_ppo(
    total_timesteps: int = 1_000_000,
    n_envs: int = 8,
    n_steps: int = 2048,
    seed: int = 0,
    checkpoint_freq: int = 50_000,
    eval_freq: int = 1_000_000,  # Effectively disable mid-training evaluation
    num_players: int = 2,
    use_curriculum: bool = False,
    curriculum_stage: int = 1,
    learning_rate: float = 3e-4,
    net_arch: list = [256, 256],
):
    """
    Train PPO with action masking for Five Towers card game.

    Args:
        total_timesteps: Total training steps
        n_envs: Number of parallel environments
        n_steps: Number of steps to run for each environment per update
        seed: Random seed
        checkpoint_freq: Save checkpoint every N steps
        eval_freq: Evaluate every N steps
        num_players: Number of players
        use_curriculum: Use curriculum learning
        curriculum_stage: Curriculum stage (1-3)
        learning_rate: Learning rate
        net_arch: Network architecture
    """
    print("=" * 60)
    print("Five Towers PPO Training")
    print("=" * 60)
    print(f"Total timesteps: {total_timesteps:,}")
    print(f"Parallel environments: {n_envs}")
    print(f"Number of players: {num_players}")
    print(f"Curriculum mode: {use_curriculum} (stage {curriculum_stage})")
    print(f"Network architecture: {net_arch}")
    print("=" * 60)

    # Create vectorized environment
    print("\n[1/5] Creating vectorized environments...")

    # Measure environment speed to choose VecEnv type
    test_env = make_env(seed, 0, num_players=num_players)()
    start = time.time()
    test_env.reset()
    for _ in range(100):
        test_env.step(test_env.action_space.sample())
    duration = time.time() - start
    test_env.close()

    step_time_ms = duration / 100 * 1000

    if step_time_ms < 5:
        print(f"  ✓ Using DummyVecEnv (step time: {step_time_ms:.2f}ms)")
        VecEnvClass = DummyVecEnv
    else:
        print(f"  ✓ Using SubprocVecEnv (step time: {step_time_ms:.2f}ms)")
        VecEnvClass = SubprocVecEnv

    # Training environments
    train_env = VecEnvClass([make_env(seed, i, num_players=num_players) for i in range(n_envs)])

    # Normalize observations (important for training stability)
    train_env = VecNormalize(
        train_env,
        norm_obs=True,
        norm_reward=False,  # Don't normalize for sparse rewards
        clip_obs=10.0,
    )

    # Evaluation environment (single env)
    eval_env = VecNormalize(
        DummyVecEnv([make_env(seed, 0, eval_env=True, num_players=num_players)]),
        norm_obs=True,
        norm_reward=False,
        clip_obs=10.0,
    )

    # Check environment (use unwrapped env)
    print("\n[2/5] Checking environment...")
    test_env_for_check = make_env(seed, 0, eval_env=True, num_players=num_players)()
    check_env(test_env_for_check)
    test_env_for_check.close()
    print("  ✓ Environment check passed")

    # Hyperparameters optimized for card games
    # Batch size calculated as n_steps * n_envs / 4 for ~4 minibatches per epoch
    # With n_steps=2048 and n_envs=8, we get 16384 transitions, batch_size=4096 gives 4 minibatches
    batch_size = max(64, (n_steps * n_envs) // 4)

    hyperparams = {
        'learning_rate': linear_schedule(learning_rate),
        'n_steps': n_steps,
        'batch_size': batch_size,
        'n_epochs': 10,
        'gamma': 0.99,
        'gae_lambda': 0.95,
        'clip_range': 0.2,
        'ent_coef': 0.01,
        'vf_coef': 0.5,
        'max_grad_norm': 0.5,
        'policy_kwargs': dict(net_arch=net_arch),
        'tensorboard_log': './tensorboard/',
        'verbose': 1,
        'seed': seed,
    }

    # Create model
    print("\n[3/5] Creating MaskablePPO model...")
    model = MaskablePPO("MlpPolicy", train_env, **hyperparams)
    print(f"  ✓ Model created with {sum(p.numel() for p in model.policy.parameters()):,} parameters")

    # Setup callbacks
    print("\n[4/5] Setting up callbacks...")

    os.makedirs('checkpoints', exist_ok=True)
    os.makedirs('best_model', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    checkpoint_callback = CheckpointCallback(
        save_freq=checkpoint_freq,
        save_path='./checkpoints/',
        name_prefix='ppo_five_towers',
    )

    # CRITICAL: Use MaskableEvalCallback, not regular EvalCallback
    eval_callback = MaskableEvalCallback(
        eval_env,
        eval_freq=eval_freq,
        n_eval_episodes=20,
        best_model_save_path='./best_model/',
        deterministic=True,
        render=False,
    )

    callbacks = [checkpoint_callback, eval_callback]

    print(f"  ✓ Checkpoints every {checkpoint_freq:,} steps")
    print(f"  ✓ Evaluation every {eval_freq:,} steps")
    print(f"  ✓ TensorBoard logging enabled")

    # Train
    print("\n[5/5] Starting training...")
    print(f"  Target: {total_timesteps:,} timesteps")
    print(f"  Estimated time: ~{total_timesteps / n_envs / 1000:.1f}k steps")
    print()

    start_time = time.time()

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=False,
        )
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
    finally:
        training_time = time.time() - start_time
        print(f"\nTraining completed in {training_time / 3600:.2f} hours")

    # Final evaluation
    print("\n" + "=" * 60)
    print("Evaluating final model...")
    print("=" * 60)

    mean_reward, std_reward = evaluate_policy(
        model,
        eval_env,
        n_eval_episodes=100,
        deterministic=True,
    )

    print(f"\nFinal evaluation: {mean_reward:.2f} +/- {std_reward:.2f}")

    # Win rate calculation (skip for now - complex with VecEnv)
    # The mean_reward already gives us a good metric
    # Positive reward means agent is winning more than losing
    print(f"Performance: {'Good' if mean_reward > 0 else 'Needs improvement'} (reward vs random)")

    # Save final model
    model.save('ppo_five_towers_final')
    print("\n✓ Model saved to ppo_five_towers_final.zip")

    # Save VecNormalize statistics
    train_env.save('vec_normalize.pkl')
    print("✓ VecNormalize statistics saved to vec_normalize.pkl")

    # Close environments
    train_env.close()
    eval_env.close()

    return model


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Train PPO for Five Towers card game',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Training parameters
    parser.add_argument(
        '--timesteps', '-t',
        type=int,
        default=1_000_000,
        help='Total training timesteps'
    )
    parser.add_argument(
        '--n-envs', '-n',
        type=int,
        default=8,
        help='Number of parallel environments'
    )
    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=0,
        help='Random seed'
    )

    # Game parameters
    parser.add_argument(
        '--players', '-p',
        type=int,
        default=2,
        choices=[2, 3, 4, 5],
        help='Number of players'
    )

    # Curriculum learning
    parser.add_argument(
        '--curriculum', '-c',
        action='store_true',
        help='Use curriculum learning'
    )
    parser.add_argument(
        '--stage',
        type=int,
        default=1,
        choices=[1, 2, 3],
        help='Curriculum stage (1=basics, 2=scoring, 3=winning)'
    )

    # Hyperparameters
    parser.add_argument(
        '--lr', '-l',
        type=float,
        default=3e-4,
        help='Learning rate'
    )
    parser.add_argument(
        '--arch',
        type=str,
        default='512,256',
        help='Network architecture (comma-separated)'
    )

    args = parser.parse_args()

    # Parse architecture
    net_arch = [int(x) for x in args.arch.split(',')]

    # Train
    train_ppo(
        total_timesteps=args.timesteps,
        n_envs=args.n_envs,
        seed=args.seed,
        num_players=args.players,
        use_curriculum=args.curriculum,
        curriculum_stage=args.stage,
        learning_rate=args.lr,
        net_arch=net_arch,
        n_steps=2048,
    )


if __name__ == '__main__':
    main()
