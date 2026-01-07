"""Game state data structures for Five Towers card game"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, UUID
import uuid


class TowerSuit(str, Enum):
    """The 5 tower suits in the game"""
    SAND = "sand"
    STONE = "stone"
    VEGETATION = "vegetation"
    WATER = "water"
    FIRE = "fire"


class GamePhase(str, Enum):
    """Game phases"""
    LOBBY = "lobby"
    BIDDING = "bidding"
    BUILDING = "building"
    SCORING = "scoring"
    GAME_OVER = "game_over"


@dataclass(frozen=True)
class Card:
    """A single card in the game"""
    id: UUID = field(default_factory=uuid.uuid4)
    suit: TowerSuit = TowerSuit.SAND
    value: int = 0

    @property
    def is_tower_top(self) -> bool:
        """Tower Top card (value 0) doubles tower points but caps tower"""
        return self.value == 0

    @property
    def is_reset(self) -> bool:
        """Reset card (value 8) accepts any card on top"""
        return self.value == 8

    @property
    def is_wild(self) -> bool:
        """Wild card (value 9) can be placed on any card"""
        return self.value == 9

    def __str__(self) -> str:
        return f"{self.suit.value.title()}:{self.value}"

    def __repr__(self) -> str:
        return f"Card({self})"


@dataclass
class Tower:
    """A player's tower for a single suit"""
    suit: TowerSuit
    cards: list[Card] = field(default_factory=list)

    @property
    def top_card(self) -> Optional[Card]:
        """The card at the top of the tower (most recently placed)"""
        return self.cards[-1] if self.cards else None

    @property
    def height(self) -> int:
        """Number of cards in the tower"""
        return len(self.cards)

    @property
    def is_capped(self) -> bool:
        """Tower is capped (has Tower Top card)"""
        return self.top_card is not None and self.top_card.is_tower_top

    @property
    def is_stuck(self) -> bool:
        """Tower is stuck (top card < 3 and no reset/wild available)"""
        if not self.top_card:
            return False
        if self.top_card.is_reset:
            return False
        return self.top_card.value < 3

    def can_place(self, card: Card) -> bool:
        """Check if a card can be placed on this tower"""
        # Empty tower always accepts
        if not self.cards:
            return True

        top = self.top_card

        # Tower Top accepts nothing
        if top.is_tower_top:
            return False

        # Reset card accepts anything
        if top.is_reset:
            return True

        # Wild card can go anywhere except on Tower Top
        if card.is_wild:
            return True

        # Standard descending rule
        return card.value < top.value

    def add_card(self, card: Card) -> None:
        """Add a card to the tower"""
        if not self.can_place(card):
            raise ValueError(f"Cannot place {card} on tower with top {self.top_card}")
        self.cards.append(card)

    def tear_down(self) -> list[Card]:
        """Remove all cards from tower and return them"""
        cards = self.cards.copy()
        self.cards.clear()
        return cards

    def calculate_score(self) -> int:
        """Calculate the score for this tower"""
        if not self.cards:
            return 0

        base_score = len(self.cards)

        # Tower Top doubles the points
        if self.top_card and self.top_card.is_tower_top:
            return base_score * 2

        return base_score


@dataclass
class PlayerState:
    """State for a single player"""
    id: UUID = field(default_factory=uuid.uuid4)
    name: str = "Player"
    towers: dict[TowerSuit, Tower] = field(default_factory=dict)
    hand: list[Card] = field(default_factory=list)  # Cards won but not yet placed
    tear_down_pile: list[Card] = field(default_factory=list)  # For penalty calculation
    current_bid: Optional[int] = None
    has_passed: bool = False

    def __post_init__(self):
        """Initialize towers for all suits"""
        if not self.towers:
            self.towers = {suit: Tower(suit=suit) for suit in TowerSuit}

    @property
    def total_score(self) -> int:
        """Calculate total score including penalties"""
        tower_scores = sum(tower.calculate_score() for tower in self.towers.values())

        # Bonus: tallest tower gets +1 per card
        max_height = max((tower.height for tower in self.towers.values()), default=0)
        if max_height > 0:
            tower_scores += max_height

        # Penalty: tear-down pile
        penalty = self.calculate_penalty()

        return tower_scores - penalty

    def calculate_penalty(self) -> int:
        """Calculate penalty from tear-down pile using triangular numbers"""
        k = len(self.tear_down_pile)
        return k * (k + 1) // 2

    def get_tower(self, suit: TowerSuit) -> Tower:
        """Get tower by suit"""
        return self.towers[suit]

    def has_tower_for(self, suit: TowerSuit) -> bool:
        """Check if player has a tower for this suit"""
        return suit in self.towers

    def can_build_tower(self, suit: TowerSuit) -> bool:
        """Check if player can build a tower for this suit"""
        return self.get_tower(suit).height == 0

    def remove_top_card(self, suit: TowerSuit) -> Optional[Card]:
        """Remove and return the top card from a tower"""
        tower = self.get_tower(suit)
        if tower.cards:
            return tower.cards.pop()
        return None


@dataclass
class GameState:
    """Complete game state"""
    phase: GamePhase = GamePhase.LOBBY
    round_number: int = 0
    deck: list[Card] = field(default_factory=list)
    display_cards: list[Card] = field(default_factory=list)  # 5 cards up for auction
    discard_pile: list[Card] = field(default_factory=list)
    players: list[PlayerState] = field(default_factory=list)
    current_player_index: int = 0
    current_high_bid: int = 0
    high_bidder_index: Optional[int] = None
    auction_winner_index: Optional[int] = None
    cards_to_process: list[Card] = field(default_factory=list)  # Cards won in auction

    @property
    def current_player(self) -> PlayerState:
        """Get the current player"""
        return self.players[self.current_player_index]

    @property
    def high_bidder(self) -> Optional[PlayerState]:
        """Get the current high bidder"""
        if self.high_bidder_index is None:
            return None
        return self.players[self.high_bidder_index]

    @property
    def auction_winner(self) -> Optional[PlayerState]:
        """Get the auction winner"""
        if self.auction_winner_index is None:
            return None
        return self.players[self.auction_winner_index]

    @property
    def active_bidders(self) -> list[PlayerState]:
        """Get players who haven't passed in current auction"""
        return [p for p in self.players if not p.has_passed]

    @property
    def is_bidding_complete(self) -> bool:
        """Check if bidding phase is complete"""
        if self.phase != GamePhase.BIDDING:
            return False
        # Bidding ends when only one player hasn't passed
        return len(self.active_bidders) <= 1

    @property
    def is_building_complete(self) -> bool:
        """Check if building phase is complete"""
        if self.phase != GamePhase.BUILDING:
            return False
        # Building ends when all cards are processed
        return len(self.cards_to_process) == 0

    @property
    def winner(self) -> Optional[PlayerState]:
        """Get the game winner (highest score)"""
        if self.phase != GamePhase.GAME_OVER:
            return None
        return max(self.players, key=lambda p: p.total_score, default=None)

    def advance_turn(self) -> None:
        """Move to next player in rotation"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def set_current_player(self, player_index: int) -> None:
        """Set the current player by index"""
        self.current_player_index = player_index % len(self.players)

    def get_player_index(self, player_id: UUID) -> int:
        """Get player index by ID"""
        for i, player in enumerate(self.players):
            if player.id == player_id:
                return i
        raise ValueError(f"Player with id {player_id} not found")

    def is_valid_bid(self, amount: int) -> bool:
        """Check if a bid amount is valid"""
        # Bid must be higher than current
        if amount <= self.current_high_bid:
            return False
        # Maximum bid is 5
        if amount > 5:
            return False
        return True

    def is_game_over(self) -> bool:
        """Check if the game is over"""
        # Game is over after deck is exhausted twice (simplified: after deck empty)
        return len(self.deck) == 0 and len(self.display_cards) == 0
