import { Card, TowerSuit } from '@vertical-victory/shared-types';

export function createStandardDeck(numPlayers: number): Card[] {
  const baseCards = 16; // 0-15 per suit
  const extraCardsPerSuit = numPlayers >= 4 ? 6 : 0; // Expansion for 4-5 players

  const deck: Card[] = [];

  for (const suit of Object.values(TowerSuit)) {
    // Base cards: 0-15
    for (let value = 0; value < baseCards; value++) {
      deck.push({
        id: crypto.randomUUID(),
        suit,
        value,
        get isTowerTop() { return this.value === 0; },
        get isReset() { return this.value === 8; },
        get isWild() { return this.value === 9; }
      });
    }

    // Extra cards for 4-5 players (values 16-21)
    for (let value = baseCards; value < baseCards + extraCardsPerSuit; value++) {
      deck.push({
        id: crypto.randomUUID(),
        suit,
        value,
        get isTowerTop() { return this.value === 0; },
        get isReset() { return this.value === 8; },
        get isWild() { return this.value === 9; }
      });
    }
  }

  return deck;
}

export function shuffleDeck(deck: readonly Card[], random: { Shuffle<T>(arr: T[]): T[] }): readonly Card[] {
  return random.Shuffle([...deck]);
}

export function dealDisplayCards(
  deck: readonly Card[],
  count: number = 5
): { deck: readonly Card[]; cards: Card[] } {
  const cards = deck.slice(0, count);
  const remaining = deck.slice(count);
  return { deck: remaining, cards };
}
