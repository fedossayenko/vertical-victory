"""Gymnasium environment for Five Towers card game"""

import gymnasium as gym
import numpy as np
from numpy.typing import NDArray
from typing import Optional, Tuple, Dict, Any

from .game_logic.state import (
    GameState,
    GamePhase,
    PlayerState,
    Card,
    TowerSuit,
)
from .game_logic.deck import create_standard_deck, deal_display_cards
from .game_logic.phases.bidding import submit_bid, submit_pass, start_new_round
from .game_logic.phases.building import place_card, tear_down_tower
from .game_logic.rules import (
    get_legal_bids,
    get_legal_placements,
    get_legal_tear_downs,
)
from .game_logic.scoring import calculate_player_score, get_winner


class FiveTowersEnv(gym.Env):
    """
    Five Towers card game environment for reinforcement learning.

    Action Space:
        Bidding Phase: Discrete(7)
        - 0: Pass
        - 1-5: Bid 1-5 cards

        Building Phase: Discrete(25) (simplified for single card)
        - 0-4: Place current card on tower 0-4 (by suit index)
        - 5-9: Tear down tower 0-4
        - 10: No action / skip

    Observation Space:
        Box(shape=(obs_size,), low=0, high=1)

        Components:
        - Display cards: 5 cards × 17 features (value 0-15 + empty)
        - Player towers: 5 towers × 3 features (height, top_value, is_capped)
        - Opponent towers: (num_players - 1) × 5 × 3
        - Auction state: 3 features (current_bid, is_winner, phase)
        - Cards to process: 5 cards × 17 features
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}

    def __init__(
        self,
        num_players: int = 2,
        render_mode: Optional[str] = None,
        max_score: int = 50,
    ):
        """Initialize the environment.

        Args:
            num_players: Number of players (2-5)
            render_mode: Rendering mode
            max_score: Maximum expected score for normalization
        """
        super().__init__()

        self.num_players = num_players
        self.max_score = max_score
        self.render_mode = render_mode

        # Calculate observation space size
        # Display cards: 5 × 17 = 85
        # Player towers: 5 × 3 = 15
        # Opponent towers: (num_players - 1) × 5 × 3
        opp_towers = (num_players - 1) * 5 * 3
        # Auction state: 3
        # Cards to process: 5 × 17 = 85
        # Phase info: 3 (one-hot for phases)
        obs_size = 85 + 15 + opp_towers + 3 + 85 + 3

        # Action space (simplified - will be masked)
        # Bidding: 6 actions (pass + bid 1-5)
        # Building: 11 actions (place on 5 towers, tear down 5 towers, skip)
        # We'll use the larger space and mask invalid actions
        self.action_space = gym.spaces.Discrete(11)

        # Observation space
        self.observation_space = gym.spaces.Box(
            low=0.0,
            high=1.0,
            shape=(obs_size,),
            dtype=np.float32,
        )

        # Game state
        self.game_state: Optional[GameState] = None
        self.player_index = 0  # The agent is always player 0

        # Track action masks
        self.action_mask: NDArray[np.float32] | None = None

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict] = None
    ) -> Tuple[NDArray[np.float32], Dict]:
        """Reset the environment.

        Args:
            seed: Random seed
            options: Additional options

        Returns:
            Initial observation and info dict
        """
        super().reset(seed=seed)

        # Create new game state
        self.game_state = GameState()

        # Create deck and players
        self.game_state.deck = create_standard_deck(self.num_players)

        for i in range(self.num_players):
            player = PlayerState(
                id=i,
                name=f"Player{i}",
            )
            self.game_state.players.append(player)

        # Deal initial display cards
        deal_display_cards(self.game_state, count=5)

        # Set phase
        self.game_state.phase = GamePhase.BIDDING
        self.game_state.current_player_index = 0
        self.game_state.round_number = 1

        # Update action mask
        self._update_action_mask()

        obs = self._get_obs()
        info = self._get_info()

        return obs, info

    def step(
        self, action: int
    ) -> Tuple[NDArray[np.float32], float, bool, bool, Dict]:
        """Execute one step in the environment.

        Args:
            action: Action to take

        Returns:
            observation, reward, terminated, truncated, info
        """
        if self.game_state is None:
            raise RuntimeError("Environment not reset")

        reward = 0.0
        terminated = False
        truncated = False

        # Get current phase
        phase = self.game_state.phase

        # Execute action based on phase
        if phase == GamePhase.BIDDING:
            reward = self._step_bidding(action)
        elif phase == GamePhase.BUILDING:
            reward = self._step_building(action)
        elif phase == GamePhase.GAME_OVER:
            terminated = True
            reward = self._get_final_reward()

        # Opponent moves (simplified - random or rule-based)
        if self.game_state.phase != GamePhase.GAME_OVER:
            self._execute_opponent_moves()

        # Update action mask
        self._update_action_mask()

        # Check termination
        if self.game_state.phase == GamePhase.GAME_OVER:
            terminated = True

        obs = self._get_obs()
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def _step_bidding(self, action: int) -> float:
        """Execute a bidding action.

        Actions:
        - 0: Pass
        - 1-5: Bid 1-5 cards

        Returns:
            Reward for this action
        """
        if action == 0:
            # Pass
            success = submit_pass(self.game_state, self.player_index)
        else:
            # Bid
            bid_amount = action
            success = submit_bid(self.game_state, self.player_index, bid_amount)

        if not success:
            # Invalid action - small penalty
            return -0.1

        # Calculate reward
        reward = 0.0

        # If won auction, potential positive reward
        if self.game_state.auction_winner_index == self.player_index:
            # Reward based on cards won
            cards_won = len(self.game_state.cards_to_process)
            reward += cards_won * 0.1

        # If passed, no immediate reward/penalty
        # (strategic value will be reflected in final score)

        return reward

    def _step_building(self, action: int) -> float:
        """Execute a building action.

        Actions:
        - 0-4: Place current card on tower 0-4 (by suit index)
        - 5-9: Tear down tower 0-4
        - 10: Skip (invalid, will be penalized)

        Returns:
            Reward for this action
        """
        if not self.game_state.cards_to_process:
            return 0.0

        current_card = self.game_state.cards_to_process[0]
        reward = 0.0

        if 0 <= action <= 4:
            # Place card on tower
            suit_idx = action
            suit = list(TowerSuit)[suit_idx]
            success = place_card(self.game_state, self.player_index, current_card, suit)

            if success:
                # Reward for successful placement
                reward += 0.1

                # Bonus for placing Tower Top
                if current_card.is_tower_top:
                    reward += 0.5
            else:
                # Invalid placement - penalty
                reward -= 0.2

        elif 5 <= action <= 9:
            # Tear down tower
            suit_idx = action - 5
            suit = list(TowerSuit)[suit_idx]
            success = tear_down_tower(self.game_state, self.player_index, suit)

            if success:
                # Penalty for tearing down (reflected in score, not immediate reward)
                reward -= 0.1
            else:
                reward -= 0.2
        else:
            # Invalid action
            reward -= 0.5

        return reward

    def _execute_opponent_moves(self) -> None:
        """Execute moves for all opponents (simplified)."""
        if self.game_state is None:
            return

        phase = self.game_state.phase

        # Execute moves for each opponent
        for i in range(self.num_players):
            if i == self.player_index:
                continue

            if phase == GamePhase.BIDDING:
                self._opponent_bidding_move(i)
            elif phase == GamePhase.BUILDING:
                if self.game_state.auction_winner_index == i:
                    self._opponent_building_move(i)

    def _opponent_bidding_move(self, player_index: int) -> None:
        """Execute a simple bidding move for opponent."""
        # Simple strategy: bid randomly if legal
        legal_bids = get_legal_bids(self.game_state, player_index)

        if legal_bids:
            # Bid lowest legal amount with some randomness
            if np.random.random() < 0.7:
                submit_bid(self.game_state, player_index, legal_bids[0])
            else:
                submit_pass(self.game_state, player_index)
        else:
            submit_pass(self.game_state, player_index)

    def _opponent_building_move(self, player_index: int) -> None:
        """Execute a simple building move for opponent."""
        if not self.game_state.cards_to_process:
            return

        card = self.game_state.cards_to_process[0]
        legal_placements = get_legal_placements(self.game_state, player_index, card)

        if legal_placements:
            # Place on first legal tower
            place_card(self.game_state, player_index, card, legal_placements[0])
        else:
            # Must tear down
            legal_tears = get_legal_tear_downs(self.game_state, player_index)
            if legal_tears:
                tear_down_tower(self.game_state, player_index, legal_tears[0])

    def _get_final_reward(self) -> float:
        """Calculate final reward based on game outcome."""
        if self.game_state is None:
            return 0.0

        agent_score = calculate_player_score(self.game_state.players[self.player_index])

        # Calculate opponent scores
        opponent_scores = [
            calculate_player_score(p)
            for i, p in enumerate(self.game_state.players)
            if i != self.player_index
        ]

        # Average opponent score
        avg_opponent_score = np.mean(opponent_scores) if opponent_scores else 0

        # Reward: score difference
        reward = (agent_score - avg_opponent_score) / self.max_score

        return reward

    def _get_obs(self) -> NDArray[np.float32]:
        """Get current observation."""
        if self.game_state is None:
            return np.zeros(self.observation_space.shape[0], dtype=np.float32)

        obs_parts = []

        # 1. Display cards (5 × 17 = 85)
        display_enc = self._encode_cards(self.game_state.display_cards, count=5)
        obs_parts.append(display_enc)

        # 2. Player towers (5 × 3 = 15)
        player = self.game_state.players[self.player_index]
        player_towers_enc = self._encode_player_towers(player)
        obs_parts.append(player_towers_enc)

        # 3. Opponent towers ((num_players - 1) × 5 × 3)
        for i, p in enumerate(self.game_state.players):
            if i != self.player_index:
                opp_towers_enc = self._encode_player_towers(p)
                obs_parts.append(opp_towers_enc)

        # 4. Auction state (3)
        auction_enc = self._encode_auction_state()
        obs_parts.append(auction_enc)

        # 5. Cards to process (5 × 17 = 85)
        cards_enc = self._encode_cards(self.game_state.cards_to_process, count=5)
        obs_parts.append(cards_enc)

        # 6. Phase info (3 - one-hot)
        phase_enc = self._encode_phase()
        obs_parts.append(phase_enc)

        # Concatenate all parts
        obs = np.concatenate(obs_parts).astype(np.float32)

        return obs

    def _encode_cards(self, cards: list[Card], count: int = 5) -> NDArray[np.float32]:
        """Encode cards as one-hot vectors.

        Args:
            cards: List of cards to encode
            count: Maximum number of cards to encode

        Returns:
            Encoded array of shape (count × 17,)
        """
        encoded = np.zeros(count * 17, dtype=np.float32)

        for i, card in enumerate(cards[:count]):
            if i >= count:
                break

            # One-hot encode value (0-15 + 1 for empty = 17)
            value_idx = min(card.value, 15)
            encoded[i * 17 + value_idx] = 1.0

        return encoded

    def _encode_player_towers(self, player: PlayerState) -> NDArray[np.float32]:
        """Encode player's towers.

        Returns:
            Encoded array of shape (5 × 3,) = [height, top_value, is_capped] for each tower
        """
        encoded = np.zeros(5 * 3, dtype=np.float32)

        for i, suit in enumerate(TowerSuit):
            tower = player.get_tower(suit)

            # Height (normalized by max expected height of 10)
            encoded[i * 3 + 0] = tower.height / 10.0

            # Top card value (normalized)
            if tower.top_card:
                encoded[i * 3 + 1] = tower.top_card.value / 15.0

            # Is capped
            encoded[i * 3 + 2] = 1.0 if tower.is_capped else 0.0

        return encoded

    def _encode_auction_state(self) -> NDArray[np.float32]:
        """Encode auction state.

        Returns:
            Encoded array of shape (3,) = [current_bid, is_winner, phase_is_bidding]
        """
        encoded = np.zeros(3, dtype=np.float32)

        # Current high bid (normalized)
        encoded[0] = self.game_state.current_high_bid / 5.0

        # Is agent the high bidder
        encoded[1] = 1.0 if self.game_state.high_bidder_index == self.player_index else 0.0

        # Is bidding phase
        encoded[2] = 1.0 if self.game_state.phase == GamePhase.BIDDING else 0.0

        return encoded

    def _encode_phase(self) -> NDArray[np.float32]:
        """Encode current phase as one-hot.

        Returns:
            One-hot encoded phase
        """
        phases = [GamePhase.BIDDING, GamePhase.BUILDING, GamePhase.GAME_OVER]
        encoded = np.zeros(len(phases), dtype=np.float32)

        try:
            idx = phases.index(self.game_state.phase)
            encoded[idx] = 1.0
        except ValueError:
            pass

        return encoded

    def action_masks(self) -> NDArray[np.bool_]:
        """
        Get action mask for invalid action masking (MaskablePPO).

        Returns:
            Boolean mask where True = valid action, False = invalid action
        """
        if self.game_state is None:
            return np.zeros(11, dtype=np.bool_)

        phase = self.game_state.phase

        if phase == GamePhase.BIDDING:
            # Mask for bidding actions (0-5: pass + bid 1-5)
            mask = np.zeros(11, dtype=np.bool_)

            # Pass is always legal if not all passed
            if len(self.game_state.active_bidders) > 1:
                mask[0] = True

            # Legal bids
            legal_bids = get_legal_bids(self.game_state, self.player_index)
            for bid in legal_bids:
                mask[bid] = True

            return mask

        elif phase == GamePhase.BUILDING:
            # Mask for building actions (0-10: 5 placements + 5 teardowns + skip)
            mask = np.zeros(11, dtype=np.bool_)

            if self.game_state.cards_to_process:
                card = self.game_state.cards_to_process[0]
                legal_placements = get_legal_placements(
                    self.game_state, self.player_index, card
                )

                # Placement actions
                for suit in legal_placements:
                    suit_idx = list(TowerSuit).index(suit)
                    mask[suit_idx] = True

                # Tear down actions
                legal_tears = get_legal_tear_downs(self.game_state, self.player_index)
                for suit in legal_tears:
                    suit_idx = list(TowerSuit).index(suit)
                    mask[5 + suit_idx] = True

            return mask

        else:
            # Game over - no valid actions
            return np.zeros(11, dtype=np.bool_)

    def _update_action_mask(self) -> None:
        """Update action mask based on current state (for info dict)."""
        if self.game_state is None:
            return

        # Get boolean mask and convert to float for info dict
        bool_mask = self.action_masks()
        self.action_mask = bool_mask.astype(np.float32)

    def _get_info(self) -> Dict:
        """Get info dictionary."""
        if self.game_state is None:
            return {}

        return {
            "phase": self.game_state.phase.value,
            "round": self.game_state.round_number,
            "action_mask": self.action_mask,
            "current_bid": self.game_state.current_high_bid,
            "cards_to_process": len(self.game_state.cards_to_process),
        }

    def render(self) -> Optional[NDArray]:
        """Render the environment."""
        if self.render_mode == "human":
            self._render_text()
        return None

    def _render_text(self) -> None:
        """Render text representation."""
        if self.game_state is None:
            print("No game state")
            return

        print(f"\n=== Round {self.game_state.round_number} ===")
        print(f"Phase: {self.game_state.phase.value}")

        if self.game_state.phase == GamePhase.BIDDING:
            print(f"Current Bid: {self.game_state.current_high_bid}")
            print(f"Display Cards: {[str(c) for c in self.game_state.display_cards]}")

        elif self.game_state.phase == GamePhase.BUILDING:
            print(f"Cards to Place: {[str(c) for c in self.game_state.cards_to_process]}")

        # Print scores
        for i, player in enumerate(self.game_state.players):
            score = calculate_player_score(player)
            print(f"Player {i}: {score} points")

    def close(self) -> None:
        """Clean up environment resources."""
        pass


# Register the environment
gym.register(id="FiveTowers-v0", entry_point=FiveTowersEnv)
