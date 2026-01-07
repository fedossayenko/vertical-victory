"""Scoring calculations for Five Towers"""

from typing import Optional

from .state import Card, GameState, PlayerState, TowerSuit


def calculate_tower_score(tower_cards: list[Card]) -> int:
    """
    Calculate the score for a single tower.

    Score = number of cards
    If Tower Top (0) is present: score × 2

    Args:
        tower_cards: List of cards in the tower (bottom to top)

    Returns:
        Tower score
    """
    if not tower_cards:
        return 0

    base_score = len(tower_cards)

    # Check for Tower Top (doubles score)
    if tower_cards[-1].value == 0:
        return base_score * 2

    return base_score


def calculate_tower_bonus(towers: dict[TowerSuit, list[Card]]) -> int:
    """
    Calculate the tallest tower bonus.

    The tower with the most cards gets +1 point per card.

    Args:
        towers: Dictionary of towers by suit

    Returns:
        Bonus points
    """
    max_height = max((len(cards) for cards in towers.values()), default=0)
    return max_height if max_height > 0 else 0


def calculate_tear_down_penalty(tear_down_count: int) -> int:
    """
    Calculate penalty using triangular numbers.

    Formula: P(x) = x(x+1)/2
    This creates exponential growth in penalty.

    Args:
        tear_down_count: Number of cards torn down

    Returns:
        Penalty score
    """
    if tear_down_count <= 0:
        return 0
    return tear_down_count * (tear_down_count + 1) // 2


def calculate_player_score(player: PlayerState) -> int:
    """
    Calculate total score for a player.

    Score = (sum of all tower scores + tallest tower bonus) - tear_down_penalty

    Args:
        player: Player state

    Returns:
        Total score
    """
    # Calculate tower scores
    tower_scores = 0
    for tower in player.towers.values():
        tower_scores += calculate_tower_score(tower.cards)

    # Calculate bonus
    bonus = calculate_tower_bonus({
        suit: tower.cards for suit, tower in player.towers.items()
    })

    # Calculate penalty
    penalty = calculate_tear_down_penalty(len(player.tear_down_pile))

    return tower_scores + bonus - penalty


def calculate_all_scores(game_state: GameState) -> dict[int, int]:
    """
    Calculate scores for all players.

    Args:
        game_state: Current game state

    Returns:
        Dictionary mapping player index to score
    """
    return {
        idx: calculate_player_score(player)
        for idx, player in enumerate(game_state.players)
    }


def get_winner(game_state: GameState) -> Optional[int]:
    """
    Get the index of the winning player (highest score).

    Args:
        game_state: Current game state

    Returns:
        Index of winning player, or None if no players
    """
    if not game_state.players:
        return None

    scores = calculate_all_scores(game_state)
    return max(scores, key=scores.get)


def get_score_rankings(game_state: GameState) -> list[tuple[int, int]]:
    """
    Get players ranked by score (highest first).

    Args:
        game_state: Current game state

    Returns:
        List of (player_index, score) tuples, sorted by score descending
    """
    scores = calculate_all_scores(game_state)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def get_score_difference(player1: PlayerState, player2: PlayerState) -> int:
    """
    Get the score difference between two players.

    Positive means player1 is winning.

    Args:
        player1: First player
        player2: Second player

    Returns:
        Score difference (player1_score - player2_score)
    """
    return calculate_player_score(player1) - calculate_player_score(player2)


def estimate_max_potential_score(
    current_tower_height: int,
    has_tower_top: bool,
    remaining_rounds: int = 10
) -> int:
    """
    Estimate the maximum potential score for a tower.

    Args:
        current_tower_height: Current tower height
        has_tower_top: Whether player has Tower Top card
        remaining_rounds: Estimated remaining rounds

    Returns:
        Estimated maximum score
    """
    # Estimate potential additional cards
    potential_growth = min(remaining_rounds, 5 - current_tower_height)
    final_height = current_tower_height + potential_growth

    # If Tower Top, score is doubled
    if has_tower_top:
        return final_height * 2

    return final_height


def get_scoring_summary(player: PlayerState) -> dict:
    """
    Get a detailed scoring breakdown for a player.

    Args:
        player: Player state

    Returns:
        Dictionary with scoring details
    """
    tower_scores = {}
    for suit, tower in player.towers.items():
        tower_scores[suit.value] = {
            "height": tower.height,
            "score": calculate_tower_score(tower.cards),
            "is_capped": tower.is_capped,
            "top_card": str(tower.top_card) if tower.top_card else None,
        }

    bonus = calculate_tower_bonus({
        suit: tower.cards for suit, tower in player.towers.items()
    })

    penalty = calculate_tear_down_penalty(len(player.tear_down_pile))

    total = sum(t["score"] for t in tower_scores.values()) + bonus - penalty

    return {
        "towers": tower_scores,
        "tallest_tower_bonus": bonus,
        "tear_down_penalty": penalty,
        "total_score": total,
    }
