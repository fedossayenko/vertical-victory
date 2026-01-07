"""Bidding phase logic for Five Towers"""

from typing import Optional

from ..state import GamePhase, GameState
from ..rules import can_bid, can_pass, is_bid_winning_bid
from . import building


def submit_bid(game_state: GameState, player_index: int, amount: int) -> bool:
    """
    Submit a bid during the bidding phase.

    Args:
        game_state: Current game state
        player_index: Index of player bidding
        amount: Bid amount (1-5, or 0 to discard)

    Returns:
        True if bid was accepted
    """
    if not can_bid(game_state, player_index, amount):
        return False

    player = game_state.players[player_index]
    player.current_bid = amount
    game_state.current_high_bid = amount
    game_state.high_bidder_index = player_index

    # Check for auto-win
    if is_bid_winning_bid(game_state, amount):
        end_auction(game_state, winner_index=player_index)
    else:
        advance_bidding_turn(game_state)

    return True


def submit_pass(game_state: GameState, player_index: int) -> bool:
    """
    Pass during the bidding phase.

    Args:
        game_state: Current game state
        player_index: Index of player passing

    Returns:
        True if pass was accepted
    """
    if not can_pass(game_state, player_index):
        return False

    player = game_state.players[player_index]
    player.has_passed = True

    # Check if only one player remains
    if len(game_state.active_bidders) == 1:
        # Last remaining player wins
        winner = game_state.active_bidders[0]
        winner_idx = game_state.get_player_index(winner.id)
        end_auction(game_state, winner_index=winner_idx)
    else:
        advance_bidding_turn(game_state)

    return True


def advance_bidding_turn(game_state: GameState) -> None:
    """
    Advance to the next player in bidding rotation.

    Skips players who have passed.
    """
    original_player = game_state.current_player_index

    # Find next active bidder
    for _ in range(len(game_state.players)):
        game_state.advance_turn()
        if not game_state.players[game_state.current_player_index].has_passed:
            break

        # Full circle - shouldn't happen with proper pass detection
        if game_state.current_player_index == original_player:
            break


def end_auction(game_state: GameState, winner_index: Optional[int] = None) -> None:
    """
    End the auction and transition to building phase.

    Args:
        game_state: Current game state
        winner_index: Index of winning player (auto-detected if None)
    """
    # Determine winner
    if winner_index is None:
        if game_state.high_bidder_index is not None:
            winner_index = game_state.high_bidder_index
        elif len(game_state.active_bidders) == 1:
            winner_index = game_state.get_player_index(game_state.active_bidders[0].id)
        else:
            # No valid winner - restart or discard
            discard_display_cards(game_state)
            return

    game_state.auction_winner_index = winner_index

    # Award cards to winner
    bid_amount = game_state.players[winner_index].current_bid or 0

    if bid_amount == 0:
        # Bid 0 = discard all display cards
        discard_display_cards(game_state)
        start_new_round(game_state)
    else:
        # Winner selects cards
        # For now, just give them the first N cards (simplified)
        # In full game, winner would choose which cards
        cards_to_award = game_state.display_cards[:bid_amount]
        game_state.cards_to_process = cards_to_award

        # Remaining cards go to discard
        remaining = game_state.display_cards[bid_amount:]
        game_state.discard_pile.extend(remaining)
        game_state.display_cards = []

    # Transition to building phase
    game_state.phase = GamePhase.BUILDING
    game_state.current_player_index = winner_index


def discard_display_cards(game_state: GameState) -> None:
    """
    Discard all cards currently on display.

    Used when everyone passes or bid is 0.
    """
    game_state.discard_pile.extend(game_state.display_cards)
    game_state.display_cards = []


def start_new_round(game_state: GameState) -> None:
    """
    Start a new bidding round.

    Deals new display cards and resets auction state.
    """
    # Reset auction state
    for player in game_state.players:
        player.current_bid = None
        player.has_passed = False
    game_state.current_high_bid = 0
    game_state.high_bidder_index = None
    game_state.auction_winner_index = None

    # Deal new cards
    from ..deck import deal_display_cards

    cards = deal_display_cards(game_state, count=5)

    if not cards:
        # No more cards - game over
        game_state.phase = GamePhase.GAME_OVER
    else:
        game_state.phase = GamePhase.BIDDING
        game_state.round_number += 1


def get_auction_status(game_state: GameState) -> dict:
    """
    Get status of the current auction.

    Returns:
        Dict with auction information
    """
    return {
        "phase": game_state.phase.value,
        "current_high_bid": game_state.current_high_bid,
        "high_bidder": game_state.high_bidder.name if game_state.high_bidder else None,
        "active_bidders": [p.name for p in game_state.active_bidders],
        "passed_players": [p.name for p in game_state.players if p.has_passed],
        "display_cards": len(game_state.display_cards),
        "round_number": game_state.round_number,
    }
