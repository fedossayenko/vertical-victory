"""Game rules and move validation for Five Towers"""

from .state import Card, GamePhase, GameState, PlayerState, TowerSuit


def can_bid(game_state: GameState, player_index: int, amount: int) -> bool:
    """
    Check if a player can make a bid.

    Rules:
    - Must be bidding phase
    - Must be player's turn
    - Player must not have passed
    - Bid must be higher than current bid
    - Maximum bid is 5

    Args:
        game_state: Current game state
        player_index: Index of player bidding
        amount: Bid amount (0-5)

    Returns:
        True if bid is valid
    """
    # Must be bidding phase
    if game_state.phase != GamePhase.BIDDING:
        return False

    # Must be player's turn
    if game_state.current_player_index != player_index:
        return False

    # Player must not have passed
    player = game_state.players[player_index]
    if player.has_passed:
        return False

    # Bid must be higher than current
    if amount <= game_state.current_high_bid:
        return False

    # Maximum bid is 5
    if amount > 5:
        return False

    return True


def can_pass(game_state: GameState, player_index: int) -> bool:
    """
    Check if a player can pass.

    Rules:
    - Must be bidding phase
    - Must be player's turn
    - Player must not have passed yet

    Args:
        game_state: Current game state
        player_index: Index of player passing

    Returns:
        True if pass is valid
    """
    # Must be bidding phase
    if game_state.phase != GamePhase.BIDDING:
        return False

    # Must be player's turn
    if game_state.current_player_index != player_index:
        return False

    # Player must not have passed yet
    player = game_state.players[player_index]
    if player.has_passed:
        return False

    return True


def can_place_card(
    game_state: GameState,
    player_index: int,
    card: Card,
    tower_suit: TowerSuit
) -> bool:
    """
    Check if a card can be placed on a tower.

    Rules:
    - Must be building phase
    - Player must be the auction winner
    - Card must be in player's hand (cards_to_process)
    - Player must not have a tower for this suit yet, OR
    - Tower must accept the card (descending, with exceptions)

    Args:
        game_state: Current game state
        player_index: Index of player placing card
        card: Card to place
        tower_suit: Suit of tower to place on

    Returns:
        True if placement is valid
    """
    # Must be building phase
    if game_state.phase != GamePhase.BUILDING:
        return False

    # Player must be auction winner
    if game_state.auction_winner_index != player_index:
        return False

    # Card must be in cards to process
    if card not in game_state.cards_to_process:
        return False

    # Get player's tower for this suit
    player = game_state.players[player_index]
    tower = player.get_tower(tower_suit)

    # Check if tower can accept card
    return tower.can_place(card)


def can_tear_down(
    game_state: GameState,
    player_index: int,
    tower_suit: TowerSuit
) -> bool:
    """
    Check if a player can tear down a tower.

    Rules:
    - Must be building phase
    - Player must be the auction winner
    - Tower must have at least 1 card

    Args:
        game_state: Current game state
        player_index: Index of player tearing down
        tower_suit: Suit of tower to tear down

    Returns:
        True if tear down is valid
    """
    # Must be building phase
    if game_state.phase != GamePhase.BUILDING:
        return False

    # Player must be auction winner
    if game_state.auction_winner_index != player_index:
        return False

    # Tower must have cards
    player = game_state.players[player_index]
    tower = player.get_tower(tower_suit)

    return tower.height > 0


def is_bid_winning_bid(game_state: GameState, amount: int) -> bool:
    """
    Check if a bid amount wins the auction immediately.

    A bid of 5 is an auto-win.

    Args:
        game_state: Current game state
        amount: Bid amount

    Returns:
        True if this bid wins immediately
    """
    return amount == 5


def validate_bid(game_state: GameState, player_index: int, amount: int) -> str:
    """
    Validate a bid and return error message if invalid.

    Args:
        game_state: Current game state
        player_index: Index of player bidding
        amount: Bid amount

    Returns:
        Empty string if valid, error message otherwise
    """
    if game_state.phase != GamePhase.BIDDING:
        return "Cannot bid outside of bidding phase"

    if game_state.current_player_index != player_index:
        return "Not your turn"

    player = game_state.players[player_index]
    if player.has_passed:
        return "You have already passed"

    if amount <= game_state.current_high_bid:
        return f"Bid must be higher than {game_state.current_high_bid}"

    if amount > 5:
        return "Maximum bid is 5"

    return ""


def validate_card_placement(
    game_state: GameState,
    player_index: int,
    card: Card,
    tower_suit: TowerSuit
) -> str:
    """
    Validate a card placement and return error message if invalid.

    Args:
        game_state: Current game state
        player_index: Index of player placing card
        card: Card to place
        tower_suit: Suit of tower to place on

    Returns:
        Empty string if valid, error message otherwise
    """
    if game_state.phase != GamePhase.BUILDING:
        return "Cannot place cards outside of building phase"

    if game_state.auction_winner_index != player_index:
        return "Only the auction winner can place cards"

    if card not in game_state.cards_to_process:
        return "Card is not in your hand"

    player = game_state.players[player_index]
    tower = player.get_tower(tower_suit)

    if not tower.can_place(card):
        if tower.is_capped:
            return "Tower is capped (has Tower Top)"
        if tower.top_card and tower.top_card.is_reset:
            return "This should not happen - reset accepts anything"
        if card.is_wild:
            return "Wild card cannot be placed on Tower Top"
        if not tower.cards:
            return "Empty tower should accept any card"
        if card.value >= tower.top_card.value:
            return f"Card value {card.value} is not less than top card {tower.top_card.value}"

    return ""


def get_legal_bids(game_state: GameState, player_index: int) -> list[int]:
    """
    Get all legal bid amounts for a player.

    Args:
        game_state: Current game state
        player_index: Index of player

    Returns:
        List of legal bid amounts
    """
    legal = []

    if game_state.phase != GamePhase.BIDDING:
        return legal

    player = game_state.players[player_index]
    if player.has_passed or game_state.current_player_index != player_index:
        return legal

    for amount in range(game_state.current_high_bid + 1, 6):  # high+1 to 5
        legal.append(amount)

    return legal


def get_legal_placements(
    game_state: GameState,
    player_index: int,
    card: Card
) -> list[TowerSuit]:
    """
    Get all legal tower suits for placing a card.

    Args:
        game_state: Current game state
        player_index: Index of player
        card: Card to place

    Returns:
        List of tower suits where card can be placed
    """
    legal = []

    if game_state.phase != GamePhase.BUILDING:
        return legal

    if game_state.auction_winner_index != player_index:
        return legal

    if card not in game_state.cards_to_process:
        return legal

    player = game_state.players[player_index]

    for suit in TowerSuit:
        tower = player.get_tower(suit)
        if tower.can_place(card):
            legal.append(suit)

    return legal


def get_legal_tear_downs(
    game_state: GameState,
    player_index: int
) -> list[TowerSuit]:
    """
    Get all tower suits that can be torn down.

    Args:
        game_state: Current game state
        player_index: Index of player

    Returns:
        List of tower suits that can be torn down
    """
    legal = []

    if game_state.phase != GamePhase.BUILDING:
        return legal

    if game_state.auction_winner_index != player_index:
        return legal

    player = game_state.players[player_index]

    for suit in TowerSuit:
        tower = player.get_tower(suit)
        if tower.height > 0:
            legal.append(suit)

    return legal


def is_game_complete(game_state: GameState) -> bool:
    """
    Check if the game is complete.

    Game is complete when:
    - Deck is empty
    - Display cards are empty
    - No cards in play

    Args:
        game_state: Current game state

    Returns:
        True if game is complete
    """
    return (
        len(game_state.deck) == 0
        and len(game_state.display_cards) == 0
        and len(game_state.cards_to_process) == 0
    )


def should_start_new_round(game_state: GameState) -> bool:
    """
    Check if a new round should start.

    New round starts when:
    - Previous round complete (building phase done)
    - Cards remain in deck or can be recycled from discard

    Args:
        game_state: Current game state

    Returns:
        True if new round should start
    """
    if game_state.phase != GamePhase.BIDDING:
        return False

    # Check if we have cards to deal
    has_cards = len(game_state.deck) > 0 or len(game_state.discard_pile) > 0

    return has_cards and len(game_state.display_cards) == 0
