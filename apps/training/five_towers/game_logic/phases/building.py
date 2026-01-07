"""Building phase logic for Five Towers"""

from typing import Optional

from ..state import Card, GamePhase, GameState, TowerSuit
from ..rules import can_place_card, can_tear_down
from ..scoring import calculate_tear_down_penalty


def place_card(
    game_state: GameState,
    player_index: int,
    card: Card,
    tower_suit: TowerSuit
) -> bool:
    """
    Place a card on a tower during the building phase.

    Args:
        game_state: Current game state
        player_index: Index of player placing card
        card: Card to place
        tower_suit: Suit of tower to place on

    Returns:
        True if card was placed
    """
    if not can_place_card(game_state, player_index, card, tower_suit):
        return False

    player = game_state.players[player_index]
    tower = player.get_tower(tower_suit)

    # Add card to tower
    tower.add_card(card)

    # Remove from cards to process
    if card in game_state.cards_to_process:
        game_state.cards_to_process.remove(card)

    # Check if building phase is complete
    if len(game_state.cards_to_process) == 0:
        end_building_phase(game_state)

    return True


def tear_down_tower(
    game_state: GameState,
    player_index: int,
    tower_suit: TowerSuit
) -> bool:
    """
    Tear down a tower (penalty action).

    Removes all cards from tower and adds them to penalty pile.
    Used when player cannot place a card legally.

    Args:
        game_state: Current game state
        player_index: Index of player tearing down
        tower_suit: Suit of tower to tear down

    Returns:
        True if tower was torn down
    """
    if not can_tear_down(game_state, player_index, tower_suit):
        return False

    player = game_state.players[player_index]
    tower = player.get_tower(tower_suit)

    # Remove all cards from tower
    removed_cards = tower.tear_down()

    # Add to penalty pile
    player.tear_down_pile.extend(removed_cards)

    return True


def end_building_phase(game_state: GameState) -> None:
    """
    End the building phase and return to bidding.

    Checks if game should continue or end.
    """
    # Check if game is over
    from ..deck import cards_remaining, deal_display_cards

    if cards_remaining(game_state) == 0:
        # Check if we can refill from discard
        from ..deck import refill_deck_from_discard

        if not refill_deck_from_discard(game_state):
            # No cards left - game over
            game_state.phase = GamePhase.GAME_OVER
            return

    # Start new round
    from .bidding import start_new_round

    start_new_round(game_state)


def auto_tear_down_if_stuck(
    game_state: GameState,
    player_index: int,
    card: Card
) -> Optional[TowerSuit]:
    """
    Check if player is stuck (cannot place card anywhere) and tear down.

    In the actual game, if player wins cards but cannot place them,
    they must tear down a tower.

    Args:
        game_state: Current game state
        player_index: Index of player
        card: Card that cannot be placed

    Returns:
        Suit of tower torn down, or None if not stuck
    """
    # Check if card can be placed anywhere
    from ..rules import get_legal_placements

    legal = get_legal_placements(game_state, player_index, card)

    if legal:
        # Not stuck - card can be placed
        return None

    # Stuck! Must tear down a tower
    # Find the best tower to tear down (lowest score)
    player = game_state.players[player_index]
    best_suit = None
    lowest_penalty = float('inf')

    for suit in TowerSuit:
        tower = player.get_tower(suit)
        if tower.height > 0:
            # Penalty for tearing down this tower
            # Current penalty + new cards from tear down
            current_penalty = calculate_tear_down_penalty(len(player.tear_down_pile))
            additional_cards = tower.height
            new_penalty = calculate_tear_down_penalty(len(player.tear_down_pile) + additional_cards)

            if new_penalty < lowest_penalty:
                lowest_penalty = new_penalty
                best_suit = suit

    # Tear down the best tower
    if best_suit is not None:
        tear_down_tower(game_state, player_index, best_suit)
        return best_suit

    return None


def get_building_status(game_state: GameState) -> dict:
    """
    Get status of the current building phase.

    Returns:
        Dict with building information
    """
    if game_state.phase != GamePhase.BUILDING:
        return {"phase": game_state.phase.value}

    winner = game_state.auction_winner

    return {
        "phase": game_state.phase.value,
        "auction_winner": winner.name if winner else None,
        "cards_to_process": len(game_state.cards_to_process),
        "cards_remaining": [
            {"suit": c.suit.value, "value": c.value}
            for c in game_state.cards_to_process
        ],
        "player_towers": {
            suit.value: {
                "height": tower.height,
                "top_card": str(tower.top_card) if tower.top_card else None,
                "is_capped": tower.is_capped,
            }
            for suit, tower in winner.towers.items()
        } if winner else {},
    }


def can_complete_building_phase(game_state: GameState) -> bool:
    """
    Check if player can complete the building phase.

    Player can complete if all cards can be placed legally.

    Args:
        game_state: Current game state

    Returns:
        True if all cards can be placed
    """
    if game_state.phase != GamePhase.BUILDING:
        return False

    if game_state.auction_winner_index is None:
        return False

    from ..rules import get_legal_placements

    player_index = game_state.auction_winner_index

    for card in game_state.cards_to_process:
        legal = get_legal_placements(game_state, player_index, card)
        if not legal:
            return False

    return True


def get_required_teardowns(game_state: GameState) -> list[TowerSuit]:
    """
    Get towers that must be torn down to place all cards.

    Returns a list of tower suits that need to be torn down
    for the player to place all their cards.

    Args:
        game_state: Current game state

    Returns:
        List of tower suits to tear down
    """
    if game_state.phase != GamePhase.BUILDING:
        return []

    if game_state.auction_winner_index is None:
        return []

    required = []
    temp_game_state = game_state  # Would need deep copy for real simulation

    # Simplified: just check which cards can't be placed
    from ..rules import get_legal_placements

    player_index = game_state.auction_winner_index

    for card in game_state.cards_to_process:
        legal = get_legal_placements(game_state, player_index, card)
        if not legal:
            # This card cannot be placed - need to tear down
            # For now, just return all non-empty towers
            player = game_state.players[player_index]
            for suit in TowerSuit:
                if player.get_tower(suit).height > 0:
                    required.append(suit)
            break

    return required
