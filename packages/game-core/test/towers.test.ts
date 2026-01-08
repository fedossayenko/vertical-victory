import { describe, it, expect } from 'vitest';
import { canPlaceCard, addCard, tearDown, calculateTowerScore } from '../src/logic/towers';
import { Card, Tower, TowerSuit } from '@vertical-victory/shared-types';

describe('Tower', () => {
  const createMockCard = (suit: TowerSuit, value: number): Card => ({
    id: `card-${suit}-${value}`,
    suit,
    value,
    get isTowerTop() { return this.value === 0; },
    get isReset() { return this.value === 8; },
    get isWild() { return this.value === 9; }
  });

  describe('canPlaceCard', () => {
    it('should accept any card on empty tower', () => {
      const tower: Tower = { suit: TowerSuit.SAND, cards: [] };
      const card = createMockCard(TowerSuit.SAND, 10);
      expect(canPlaceCard(tower, card)).toBe(true);
    });

    it('should accept cards in descending order', () => {
      const cards = [createMockCard(TowerSuit.SAND, 15), createMockCard(TowerSuit.SAND, 10)];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards
      };
      const nextCard = createMockCard(TowerSuit.SAND, 5);
      expect(canPlaceCard(tower, nextCard)).toBe(true);
    });

    it('should reject cards in ascending order', () => {
      const cards = [createMockCard(TowerSuit.SAND, 10)];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards
      };
      const nextCard = createMockCard(TowerSuit.SAND, 15);
      expect(canPlaceCard(tower, nextCard)).toBe(false);
    });

    it('should reject cards on capped tower', () => {
      const towerTop = createMockCard(TowerSuit.SAND, 0);
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards: [towerTop],
        height: 1,
        isCapped: true
      };
      const card = createMockCard(TowerSuit.SAND, 5);
      expect(canPlaceCard(tower, card)).toBe(false);
    });

    it('should accept any card on Reset card (value 8)', () => {
      const cards = [createMockCard(TowerSuit.SAND, 8)];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards
      };
      const highCard = createMockCard(TowerSuit.SAND, 15);
      expect(canPlaceCard(tower, highCard)).toBe(true);
    });

    it('should accept Wild card (value 9) on any non-capped tower', () => {
      const cards = [createMockCard(TowerSuit.SAND, 5)];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards
      };
      const wildCard = createMockCard(TowerSuit.SAND, 9);
      expect(canPlaceCard(tower, wildCard)).toBe(true);
    });
  });

  describe('addCard', () => {
    it('should add card to empty tower', () => {
      const tower: Tower = { suit: TowerSuit.SAND, cards: [] };
      const card = createMockCard(TowerSuit.SAND, 10);
      const newTower = addCard(tower, card);
      expect(newTower.cards.length).toBe(1);
      expect(newTower.cards[0]).toBe(card);
    });

    it('should add card to existing tower', () => {
      const cards = [createMockCard(TowerSuit.SAND, 10)];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards
      };
      const newCard = createMockCard(TowerSuit.SAND, 5);
      const newTower = addCard(tower, newCard);
      expect(newTower.cards.length).toBe(2);
      expect(newTower.cards[1]).toBe(newCard);
    });

    it('should not mutate original tower', () => {
      const tower: Tower = { suit: TowerSuit.SAND, cards: [] };
      const card = createMockCard(TowerSuit.SAND, 10);
      const originalLength = tower.cards.length;
      addCard(tower, card);
      expect(tower.cards.length).toBe(originalLength);
    });
  });

  describe('tearDown', () => {
    it('should tear down tower with cards', () => {
      const cards = [
        createMockCard(TowerSuit.SAND, 15),
        createMockCard(TowerSuit.SAND, 10),
        createMockCard(TowerSuit.SAND, 5)
      ];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards,
        height: 3,
        isCapped: false
      };
      const { tower: newTower, cards: removedCards } = tearDown(tower);
      expect(newTower.cards.length).toBe(0);
      expect(removedCards.length).toBe(3);
    });

    it('should tear down empty tower', () => {
      const tower: Tower = { suit: TowerSuit.SAND, cards: [] };
      const { tower: newTower, cards } = tearDown(tower);
      expect(newTower.cards.length).toBe(0);
      expect(cards.length).toBe(0);
    });
  });

  describe('calculateTowerScore', () => {
    it('should return 0 for empty tower', () => {
      const tower: Tower = { suit: TowerSuit.SAND, cards: [] };
      expect(calculateTowerScore(tower)).toBe(0);
    });

    it('should calculate score based on height', () => {
      const cards = [
        createMockCard(TowerSuit.SAND, 10),
        createMockCard(TowerSuit.SAND, 5),
        createMockCard(TowerSuit.SAND, 3)
      ];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards,
        height: 3,
        isCapped: false
      };
      expect(calculateTowerScore(tower)).toBe(3);
    });

    it('should double score when capped', () => {
      const cards = [
        createMockCard(TowerSuit.SAND, 10),
        createMockCard(TowerSuit.SAND, 5),
        createMockCard(TowerSuit.SAND, 0)
      ];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards,
        height: 3,
        isCapped: true
      };
      expect(calculateTowerScore(tower)).toBe(6);
    });

    it('should double score for tall capped tower', () => {
      const cards = [
        createMockCard(TowerSuit.SAND, 15),
        createMockCard(TowerSuit.SAND, 12),
        createMockCard(TowerSuit.SAND, 10),
        createMockCard(TowerSuit.SAND, 8),
        createMockCard(TowerSuit.SAND, 5),
        createMockCard(TowerSuit.SAND, 0)
      ];
      const tower: Tower = {
        suit: TowerSuit.SAND,
        cards,
        height: 6,
        isCapped: true
      };
      expect(calculateTowerScore(tower)).toBe(12);
    });
  });
});
