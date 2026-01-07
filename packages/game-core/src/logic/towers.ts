import { Card, Tower, TowerSuit } from '@vertical-victory/shared-types';
import { produce } from 'immer';

export function canPlaceCard(tower: Tower, card: Card): boolean {
  // Empty tower accepts any card
  if (tower.cards.length === 0) return true;

  // Tower Top (value 0) caps the tower
  if (tower.isCapped) return false;

  const topCard = tower.cards[tower.cards.length - 1];

  // Reset card (value 8) accepts anything
  if (topCard.isReset) return true;

  // Wild card (value 9) can go anywhere except on Tower Top
  if (card.isWild) return !tower.isCapped;

  // Standard rule: descending order
  return card.value < topCard.value;
}

export function addCard(tower: Tower, card: Card): Tower {
  return produce(tower, draft => {
    draft.cards = [...draft.cards, card];
  });
}

export function tearDown(tower: Tower): { tower: Tower; cards: Card[] } {
  const cards = [...tower.cards];
  const newTower: Tower = {
    ...tower,
    cards: []
  };
  return { tower: newTower, cards };
}

export function calculateTowerScore(tower: Tower): number {
  if (tower.cards.length === 0) return 0;

  const baseScore = tower.cards.length;
  return tower.isCapped ? baseScore * 2 : baseScore;
}
