"""Reward shaping utilities for Five Towers training"""

import numpy as np
from typing import Optional

from ..game_logic.state import GameState, GamePhase, PlayerState, Card
from ..game_logic.scoring import calculate_player_score


class RewardShaper:
    """
    Reward shaping for Five Towers card game.

    Uses potential-based reward shaping to avoid altering optimal policy
    while providing informative feedback for learning.
    """

    def __init__(
        self,
        gamma: float = 0.99,
        use_shaped_rewards: bool = True,
        reward_scale: float = 1.0,
    ):
        """
        Initialize reward shaper.

        Args:
            gamma: Discount factor for potential-based shaping
            use_shaped_rewards: Whether to use shaped rewards
            reward_scale: Scaling factor for all rewards
        """
        self.gamma = gamma
        self.use_shaped_rewards = use_shaped_rewards
        self.reward_scale = reward_scale

    def compute_reward(
        self,
        game_state: GameState,
        player_index: int,
        action: int,
        next_state: Optional[GameState] = None,
    ) -> float:
        """
        Compute shaped reward for an action.

        Args:
            game_state: Current game state
            player_index: Index of player taking action
            action: Action taken
            next_state: Next game state (after action)

        Returns:
            Shaped reward value
        """
        if not self.use_shaped_rewards:
            # Use sparse reward (only final score matters)
            return self._compute_sparse_reward(game_state, player_index)

        # Potential-based reward shaping
        current_potential = self._compute_potential(game_state, player_index)

        if next_state is not None:
            next_potential = self._compute_potential(next_state, player_index)
            shaped_reward = (
                self._compute_base_reward(game_state, player_index, action)
                + self.gamma * next_potential
                - current_potential
            )
        else:
            shaped_reward = (
                self._compute_base_reward(game_state, player_index, action)
                - current_potential
            )

        return shaped_reward * self.reward_scale

    def _compute_base_reward(
        self, game_state: GameState, player_index: int, action: int
    ) -> float:
        """Compute base reward without shaping."""
        phase = game_state.phase

        if phase == GamePhase.GAME_OVER:
            return self._compute_game_over_reward(game_state, player_index)

        elif phase == GamePhase.BIDDING:
            return self._compute_bidding_reward(game_state, player_index, action)

        elif phase == GamePhase.BUILDING:
            return self._compute_building_reward(game_state, player_index, action)

        return 0.0

    def _compute_sparse_reward(
        self, game_state: GameState, player_index: int
    ) -> float:
        """Compute sparse reward (only at game end)."""
        if game_state.phase == GamePhase.GAME_OVER:
            return self._compute_game_over_reward(game_state, player_index)
        return 0.0

    def _compute_potential(self, game_state: GameState, player_index: int) -> float:
        """
        Compute potential (state value) for potential-based reward shaping.

        Potential represents the expected future value from this state.
        """
        player = game_state.players[player_index]

        # Base potential: current score
        score = calculate_player_score(player)

        # Add heuristics for game position
        potential = score / 50.0  # Normalize to roughly 0-1 range

        phase = game_state.phase

        if phase == GamePhase.BIDDING:
            # Bidding potential: based on cards remaining and position
            remaining_cards = len(game_state.deck) + len(game_state.discard_pile)
            total_cards = 80 if game_state.num_players <= 3 else 110
            game_progress = 1.0 - (remaining_cards / total_cards)

            # Early game: more potential
            potential *= (1.0 + game_progress * 0.5)

        elif phase == GamePhase.BUILDING:
            # Building potential: based on cards to process
            cards_to_process = len(game_state.cards_to_process)

            # Fewer cards to process = higher potential (close to completing)
            if cards_to_process > 0:
                potential += 0.1 * (1.0 - cards_to_process / 5.0)
            else:
                potential += 0.1  # Bonus for completing building phase

        return np.clip(potential, -1.0, 1.0)

    def _compute_game_over_reward(
        self, game_state: GameState, player_index: int
    ) -> float:
        """Compute reward at game end."""
        player_score = calculate_player_score(game_state.players[player_index])

        # Calculate opponent scores
        opponent_scores = [
            calculate_player_score(p)
            for i, p in enumerate(game_state.players)
            if i != player_index
        ]

        if not opponent_scores:
            return player_score / 50.0

        # Reward based on relative performance
        avg_opponent_score = np.mean(opponent_scores)
        score_diff = player_score - avg_opponent_score

        # Normalize to roughly [-1, 1] range
        return np.clip(score_diff / 20.0, -1.0, 1.0)

    def _compute_bidding_reward(
        self, game_state: GameState, player_index: int, action: int
    ) -> float:
        """Compute reward during bidding phase."""
        player = game_state.players[player_index]

        # Small reward for winning auction
        if game_state.auction_winner_index == player_index:
            cards_won = len(game_state.cards_to_process)
            return cards_won * 0.05

        # Small penalty for passing (opportunity cost)
        if action == 0:  # Pass
            return -0.02

        # Small reward for bidding (encourages participation)
        return 0.01

    def _compute_building_reward(
        self, game_state: GameState, player_index: int, action: int
    ) -> float:
        """Compute reward during building phase."""
        if not game_state.cards_to_process:
            return 0.0

        current_card = game_state.cards_to_process[0]

        # Card placement actions (0-4)
        if 0 <= action <= 4:
            # Check if placement was successful
            player = game_state.players[player_index]
            tower = player.get_tower(list(game_state.players[player_index].towers.keys())[action])

            if tower.cards and tower.cards[-1] == current_card:
                # Successfully placed card
                reward = 0.05

                # Bonus for strategic cards
                if current_card.is_tower_top:
                    reward += 0.2
                elif current_card.is_reset:
                    reward += 0.1
                elif current_card.is_wild:
                    reward += 0.15

                # Bonus for completing tower
                if tower.is_capped:
                    reward += 0.1

                return reward
            else:
                # Failed placement
                return -0.1

        # Tear down actions (5-9)
        elif 5 <= action <= 9:
            # Tear down is generally bad (penalty)
            # But sometimes necessary
            return -0.05

        # Invalid action
        return -0.2


class CurriculumRewardShaper(RewardShaper):
    """
    Curriculum learning reward shaper.

    Adjusts reward focus based on training stage:
    - Stage 1: Focus on legal moves
    - Stage 2: Focus on scoring
    - Stage 3: Focus on winning
    """

    def __init__(self, stage: int = 1, **kwargs):
        """
        Initialize curriculum reward shaper.

        Args:
            stage: Curriculum stage (1, 2, or 3)
            **kwargs: Arguments passed to RewardShaper
        """
        super().__init__(**kwargs)
        self.stage = stage

    def compute_reward(
        self,
        game_state: GameState,
        player_index: int,
        action: int,
        next_state: Optional[GameState] = None,
    ) -> float:
        """Compute curriculum-aware reward."""
        # Stage 1: Focus on legal moves and basic gameplay
        if self.stage == 1:
            # Higher penalty for illegal moves
            # Focus on understanding game mechanics
            base_reward = super().compute_reward(
                game_state, player_index, action, next_state
            )

            # Reduce focus on winning, increase focus on legality
            return base_reward * 0.5

        # Stage 2: Focus on scoring
        elif self.stage == 2:
            # Emphasize intermediate rewards
            # Encourage tower building
            return super().compute_reward(
                game_state, player_index, action, next_state
            ) * 1.2

        # Stage 3: Focus on winning (full rewards)
        else:
            return super().compute_reward(
                game_state, player_index, action, next_state
            )


def create_reward_shaper(
    curriculum_mode: bool = False,
    stage: int = 1,
    **kwargs
) -> RewardShaper:
    """
    Factory function to create reward shaper.

    Args:
        curriculum_mode: Whether to use curriculum learning
        stage: Curriculum stage (if curriculum_mode=True)
        **kwargs: Arguments passed to RewardShaper

    Returns:
        Configured reward shaper
    """
    if curriculum_mode:
        return CurriculumRewardShaper(stage=stage, **kwargs)
    else:
        return RewardShaper(**kwargs)
