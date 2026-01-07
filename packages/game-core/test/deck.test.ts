import { describe, it, expect, beforeEach } from 'vitest';
import { createStandardDeck, shuffleDeck, dealDisplayCards } from '../src/logic/deck';
import { TowerSuit } from '@vertical-victory/shared-types';

describe('Deck', () => {
  it('should create 80 cards for 2-3 players', () => {
    const deck = createStandardDeck(2);
    expect(deck.length).toBe(80);
  });

  it('should create 80 cards for 3 players', () => {
    const deck = createStandardDeck(3);
    expect(deck.length).toBe(80);
  });

  it('should create 110 cards for 4-5 players', () => {
    const deck = createStandardDeck(4);
    expect(deck.length).toBe(110);
  });

  it('should have all 5 suits represented', () => {
    const deck = createStandardDeck(2);
    const suits = new Set(deck.map(c => c.suit));
    expect(suits.size).toBe(5);
  });

  it('should have card values 0-15', () => {
    const deck = createStandardDeck(2);
    const values = deck.map(c => c.value);
    expect(Math.min(...values)).toBe(0);
    expect(Math.max(...values)).toBe(15);
  });

  it('should have 16 cards per suit', () => {
    const deck = createStandardDeck(2);
    const sandCards = deck.filter(c => c.suit === TowerSuit.SAND);
    expect(sandCards.length).toBe(16);
  });

  it('should identify Tower Top cards (value 0)', () => {
    const deck = createStandardDeck(2);
    const towerTops = deck.filter(c => c.isTowerTop);
    expect(towerTops.length).toBe(5); // One per suit
    expect(towerTops.every(c => c.value === 0)).toBe(true);
  });

  it('should identify Reset cards (value 8)', () => {
    const deck = createStandardDeck(2);
    const resetCards = deck.filter(c => c.isReset);
    expect(resetCards.length).toBe(5); // One per suit
    expect(resetCards.every(c => c.value === 8)).toBe(true);
  });

  it('should identify Wild cards (value 9)', () => {
    const deck = createStandardDeck(2);
    const wildCards = deck.filter(c => c.isWild);
    expect(wildCards.length).toBe(5); // One per suit
    expect(wildCards.every(c => c.value === 9)).toBe(true);
  });

  it('should shuffle deck deterministically', () => {
    const deck = createStandardDeck(2);
    const mockRandom = {
      Shuffle: <T>(arr: T[]): T[] => arr.reverse()
    };
    const shuffled = shuffleDeck(deck, mockRandom);
    expect(shuffled.length).toBe(deck.length);
    expect(shuffled[0]).not.toBe(deck[0]);
  });

  it('should deal display cards correctly', () => {
    const deck = createStandardDeck(2);
    const result = dealDisplayCards(deck, 5);
    expect(result.cards.length).toBe(5);
    expect(result.deck.length).toBe(75);
  });

  it('should deal less cards if deck is small', () => {
    const smallDeck = createStandardDeck(2).slice(0, 3);
    const result = dealDisplayCards(smallDeck, 5);
    expect(result.cards.length).toBe(3);
    expect(result.deck.length).toBe(0);
  });
});
