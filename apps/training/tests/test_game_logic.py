"""Tests for core game logic"""

import pytest
from five_towers.game_logic.state import (
    Card,
    TowerSuit,
    Tower,
    PlayerState,
    GameState,
    GamePhase,
)
from five_towers.game_logic.deck import create_standard_deck, deal_display_cards
from five_towers.game_logic.scoring import (
    calculate_tower_score,
    calculate_tear_down_penalty,
    calculate_player_score,
)


class TestCard:
    """Test Card functionality"""

    def test_card_creation(self):
        """Test creating a card"""
        card = Card(suit=TowerSuit.SAND, value=5)
        assert card.suit == TowerSuit.SAND
        assert card.value == 5

    def test_tower_top(self):
        """Test Tower Top card (value 0)"""
        card = Card(suit=TowerSuit.SAND, value=0)
        assert card.is_tower_top is True
        assert card.is_reset is False
        assert card.is_wild is False

    def test_reset_card(self):
        """Test Reset card (value 8)"""
        card = Card(suit=TowerSuit.SAND, value=8)
        assert card.is_tower_top is False
        assert card.is_reset is True
        assert card.is_wild is False

    def test_wild_card(self):
        """Test Wild card (value 9)"""
        card = Card(suit=TowerSuit.SAND, value=9)
        assert card.is_tower_top is False
        assert card.is_reset is False
        assert card.is_wild is True


class TestTower:
    """Test Tower functionality"""

    def test_empty_tower(self):
        """Test empty tower"""
        tower = Tower(suit=TowerSuit.SAND)
        assert tower.height == 0
        assert tower.top_card is None
        assert tower.is_capped is False

    def test_add_card(self):
        """Test adding card to tower"""
        tower = Tower(suit=TowerSuit.SAND)
        card1 = Card(suit=TowerSuit.SAND, value=10)
        card2 = Card(suit=TowerSuit.SAND, value=5)

        tower.add_card(card1)
        assert tower.height == 1
        assert tower.top_card == card1

        tower.add_card(card2)
        assert tower.height == 2
        assert tower.top_card == card2

    def test_can_place_descending(self):
        """Test descending placement rule"""
        tower = Tower(suit=TowerSuit.SAND)
        card1 = Card(suit=TowerSuit.SAND, value=10)
        card2 = Card(suit=TowerSuit.SAND, value=5)
        card3 = Card(suit=TowerSuit.SAND, value=7)  # Invalid

        tower.add_card(card1)
        assert tower.can_place(card2) is True
        assert tower.can_place(card3) is False

    def test_can_place_wild(self):
        """Test wild card placement"""
        tower = Tower(suit=TowerSuit.SAND)
        card = Card(suit=TowerSuit.SAND, value=10)
        wild = Card(suit=TowerSuit.SAND, value=9)

        tower.add_card(card)
        assert tower.can_place(wild) is True

    def test_can_place_on_reset(self):
        """Test placement on reset card"""
        tower = Tower(suit=TowerSuit.SAND)
        card1 = Card(suit=TowerSuit.SAND, value=8)  # Reset
        card2 = Card(suit=TowerSuit.SAND, value=15)  # Higher value

        tower.add_card(card1)
        assert tower.can_place(card2) is True

    def test_tower_top_capping(self):
        """Test that Tower Top caps the tower"""
        tower = Tower(suit=TowerSuit.SAND)
        card1 = Card(suit=TowerSuit.SAND, value=5)
        card2 = Card(suit=TowerSuit.SAND, value=0)  # Tower Top
        card3 = Card(suit=TowerSuit.SAND, value=3)

        tower.add_card(card1)
        tower.add_card(card2)

        assert tower.is_capped is True
        assert tower.can_place(card3) is False

    def test_tear_down(self):
        """Test tearing down a tower"""
        tower = Tower(suit=TowerSuit.SAND)
        card1 = Card(suit=TowerSuit.SAND, value=10)
        card2 = Card(suit=TowerSuit.SAND, value=5)

        tower.add_card(card1)
        tower.add_card(card2)

        cards = tower.tear_down()
        assert len(cards) == 2
        assert tower.height == 0
        assert tower.top_card is None


class TestScoring:
    """Test scoring calculations"""

    def test_empty_tower_score(self):
        """Test scoring empty tower"""
        assert calculate_tower_score([]) == 0

    def test_basic_tower_score(self):
        """Test basic tower scoring"""
        cards = [
            Card(suit=TowerSuit.SAND, value=10),
            Card(suit=TowerSuit.SAND, value=5),
            Card(suit=TowerSuit.SAND, value=3),
        ]
        assert calculate_tower_score(cards) == 3

    def test_tower_top_doubles(self):
        """Test that Tower Top doubles the score"""
        cards = [
            Card(suit=TowerSuit.SAND, value=10),
            Card(suit=TowerSuit.SAND, value=5),
            Card(suit=TowerSuit.SAND, value=0),  # Tower Top
        ]
        assert calculate_tower_score(cards) == 6  # 3 cards × 2

    def test_tear_down_penalty(self):
        """Test tear down penalty calculation"""
        assert calculate_tear_down_penalty(0) == 0
        assert calculate_tear_down_penalty(1) == 1  # 1
        assert calculate_tear_down_penalty(2) == 3  # 1 + 2
        assert calculate_tear_down_penalty(3) == 6  # 1 + 2 + 3
        assert calculate_tear_down_penalty(5) == 15  # 5 × 6 / 2

    def test_player_score(self):
        """Test complete player score calculation"""
        player = PlayerState(id=0, name="Test")

        # Add some cards to towers
        sand_tower = player.get_tower(TowerSuit.SAND)
        sand_tower.add_card(Card(suit=TowerSuit.SAND, value=10))
        sand_tower.add_card(Card(suit=TowerSuit.SAND, value=5))

        fire_tower = player.get_tower(TowerSuit.FIRE)
        fire_tower.add_card(Card(suit=TowerSuit.FIRE, value=8))
        fire_tower.add_card(Card(suit=TowerSuit.FIRE, value=3))
        fire_tower.add_card(Card(suit=TowerSuit.FIRE, value=0))  # Tower Top

        score = calculate_player_score(player)
        assert score == 9  # (2 + 3×2) + 3 bonus - 0 penalty


class TestDeck:
    """Test deck generation and management"""

    def test_standard_deck_size_2_players(self):
        """Test deck size for 2 players"""
        deck = create_standard_deck(num_players=2)
        assert len(deck) == 80  # Base set only

    def test_standard_deck_size_4_players(self):
        """Test deck size for 4+ players"""
        deck = create_standard_deck(num_players=4)
        assert len(deck) == 110  # Base set + expansion

    def test_deck_has_all_suits(self):
        """Test that deck contains all suits"""
        deck = create_standard_deck(num_players=2)
        suits = {card.suit for card in deck}
        assert len(suits) == 5
        assert TowerSuit.SAND in suits
        assert TowerSuit.STONE in suits
        assert TowerSuit.VEGETATION in suits
        assert TowerSuit.WATER in suits
        assert TowerSuit.FIRE in suits

    def test_deck_has_all_values(self):
        """Test that deck has cards 0-15"""
        deck = create_standard_deck(num_players=2)
        values = {card.value for card in deck}
        assert len(values) == 16
        assert all(v in values for v in range(16))


class TestGameState:
    """Test game state management"""

    def test_initial_state(self):
        """Test initial game state"""
        state = GameState()
        assert state.phase == GamePhase.LOBBY
        assert state.round_number == 0
        assert len(state.players) == 0
        assert len(state.deck) == 0

    def test_add_players(self):
        """Test adding players to game"""
        state = GameState()
        state.players.append(PlayerState(id=0, name="Player0"))
        state.players.append(PlayerState(id=1, name="Player1"))

        assert len(state.players) == 2
        assert state.current_player_index == 0

    def test_advance_turn(self):
        """Test turn advancement"""
        state = GameState()
        state.players.append(PlayerState(id=0, name="Player0"))
        state.players.append(PlayerState(id=1, name="Player1"))

        state.advance_turn()
        assert state.current_player_index == 1

        state.advance_turn()
        assert state.current_player_index == 0

    def test_is_valid_bid(self):
        """Test bid validation"""
        state = GameState()
        state.current_high_bid = 2

        assert state.is_valid_bid(3) is True
        assert state.is_valid_bid(2) is False  # Must be higher
        assert state.is_valid_bid(6) is False  # Max is 5

    def test_active_bidders(self):
        """Test active bidders calculation"""
        state = GameState()
        state.players.append(PlayerState(id=0, name="Player0"))
        state.players.append(PlayerState(id=1, name="Player1"))
        state.players.append(PlayerState(id=2, name="Player2"))

        # Initially all active
        assert len(state.active_bidders) == 3

        # One player passes
        state.players[0].has_passed = True
        assert len(state.active_bidders) == 2

        # Second player passes
        state.players[1].has_passed = True
        assert len(state.active_bidders) == 1
        assert state.is_bidding_complete is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
