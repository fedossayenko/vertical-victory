"""Deck generation and management for Five Towers"""

import random
from typing import Optional

from .state import Card, GameState, TowerSuit


def create_standard_deck(num_players: int = 2) -> list[Card]:
    """
    Create a standard deck for Five Towers.

    Deck composition:
    - 5 suits (towers)
    - Each suit has cards 0-15 (16 cards per suit)
    - 4-5 players: 110 cards (extra copies of certain cards)
    - 2-3 players: 80 cards (base set only)

    Args:
        num_players: Number of players (affects deck size)

    Returns:
        Shuffled deck of cards
    """
    deck = []

    # Base set: 1 of each card 0-15 per suit = 16 cards * 5 suits = 80 cards
    for suit in TowerSuit:
        for value in range(16):  # 0-15
            deck.append(Card(suit=suit, value=value))

    # Expansion set for 4-5 players (30 additional cards)
    if num_players >= 4:
        # Add extra copies of strategic cards
        # Extra 0 cards (Tower Top) - 1 per suit = 5 cards
        for suit in TowerSuit:
            deck.append(Card(suit=suit, value=0))

        # Extra 8 cards (Reset) - 1 per suit = 5 cards
        for suit in TowerSuit:
            deck.append(Card(suit=suit, value=8))

        # Extra mid-range cards for balance - 4 per suit = 20 cards
        # Values: 5, 6, 7, 10 (strategic mid-range cards)
        for suit in TowerSuit:
            deck.append(Card(suit=suit, value=5))
            deck.append(Card(suit=suit, value=6))
            deck.append(Card(suit=suit, value=7))
            deck.append(Card(suit=suit, value=10))

    # Shuffle the deck
    random.shuffle(deck)

    return deck


def deal_display_cards(game_state: GameState, count: int = 5) -> list[Card]:
    """
    Deal cards from deck to display for auction.

    Args:
        game_state: Current game state
        count: Number of cards to deal (default 5)

    Returns:
        List of dealt cards
    """
    cards = []
    for _ in range(count):
        if game_state.deck:
            card = game_state.deck.pop()
            cards.append(card)
        else:
            # Deck is empty - this should trigger game over check
            break

    game_state.display_cards = cards
    return cards


def return_cards_to_deck(game_state: GameState, cards: list[Card]) -> None:
    """
    Return cards to the bottom of the deck.

    Args:
        game_state: Current game state
        cards: Cards to return
    """
    for card in cards:
        game_state.deck.insert(0, card)


def move_cards_to_discard(game_state: GameState, cards: list[Card]) -> None:
    """
    Move cards to discard pile.

    Args:
        game_state: Current game state
        cards: Cards to discard
    """
    game_state.discard_pile.extend(cards)


def shuffle_deck(game_state: GameState) -> None:
    """
    Shuffle the deck in place.

    Args:
        game_state: Current game state
    """
    random.shuffle(game_state.deck)


def draw_cards(game_state: GameState, count: int = 1) -> list[Card]:
    """
    Draw cards from the deck.

    Args:
        game_state: Current game state
        count: Number of cards to draw

    Returns:
        List of drawn cards (may be fewer if deck is low)
    """
    cards = []
    for _ in range(count):
        if game_state.deck:
            cards.append(game_state.deck.pop())
        else:
            break
    return cards


def deal_initial_hands(game_state: GameState) -> None:
    """
    Deal initial hands to all players (if starting with cards).

    Note: Standard 5 Towers starts with empty hands,
    but this can be used for variants.

    Args:
        game_state: Current game state
    """
    # Standard game: no initial hands
    # This is a placeholder for variants
    pass


def refill_deck_from_discard(game_state: GameState) -> bool:
    """
    Shuffle discard pile back into deck when deck is empty.

    Args:
        game_state: Current game state

    Returns:
        True if deck was refilled, False if no cards to refill
    """
    if not game_state.discard_pile:
        return False

    game_state.deck = game_state.discard_pile.copy()
    game_state.discard_pile.clear()
    shuffle_deck(game_state)
    return True


def cards_remaining(game_state: GameState) -> int:
    """Get number of cards remaining in deck"""
    return len(game_state.deck)


def discard_pile_size(game_state: GameState) -> int:
    """Get size of discard pile"""
    return len(game_state.discard_pile)


def get_deck_summary(game_state: GameState) -> dict:
    """
    Get a summary of deck composition.

    Returns:
        Dict with counts by suit and value
    """
    summary = {
        "total": len(game_state.deck),
        "by_suit": {suit.value: 0 for suit in TowerSuit},
        "by_value": {},
    }

    for card in game_state.deck:
        summary["by_suit"][card.suit.value] += 1
        summary["by_value"][card.value] = summary["by_value"].get(card.value, 0) + 1

    return summary
