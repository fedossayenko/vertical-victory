import { describe, it, expect } from 'vitest';
import { calculatePlayerScore, calculateTearDownPenalty, getScoreRankings } from '../src/logic/scoring';
import { PlayerState, Tower, TowerSuit } from '@vertical-victory/shared-types';

describe('Scoring', () => {
  const createMockTower = (cards: number[]): Tower => ({
    suit: TowerSuit.SAND,
    cards: cards.map((v, i) => ({
      id: `card-${i}`,
      suit: TowerSuit.SAND,
      value: v,
      get isTowerTop() { return this.value === 0; },
      get isReset() { return this.value === 8; },
      get isWild() { return this.value === 9; }
    })),
    height: cards.length,
    isCapped: cards.includes(0)
  });

  const createMockPlayer = (
    id: string,
    towerCards: Record<string, number[]>,
    tearDownCount: number
  ): PlayerState => ({
    id,
    name: `Test Player ${id}`,
    towers: {
      sand: createMockTower(towerCards.sand || []),
      stone: createMockTower(towerCards.stone || []),
      vegetation: createMockTower(towerCards.vegetation || []),
      water: createMockTower(towerCards.water || []),
      fire: createMockTower(towerCards.fire || [])
    },
    hand: [],
    tearDownPile: Array(tearDownCount).fill(null).map((_, i) => ({
      id: `teardown-${i}`,
      suit: TowerSuit.SAND,
      value: i,
      get isTowerTop() { return false; },
      get isReset() { return false; },
      get isWild() { return false; }
    })),
    currentBid: null,
    hasPassed: false,
    totalScore: 0
  });

  describe('calculatePlayerScore', () => {
    it('should calculate score for player with no towers', () => {
      const player = createMockPlayer('0', {}, 0);
      expect(calculatePlayerScore(player)).toBe(0);
    });

    it('should calculate score for player with uncapped towers', () => {
      const player = createMockPlayer('0', {
        sand: [10, 5, 3],
        stone: [8, 4],
        water: [15]
      }, 0);
      expect(calculatePlayerScore(player)).toBe(9); // 3+2+1+3(maxHeight)
    });

    it('should double score for capped towers', () => {
      const player = createMockPlayer('0', {
        sand: [10, 5, 0], // Capped: 3*2=6
        stone: [8, 4]      // Uncapped: 2
      }, 0);
      expect(calculatePlayerScore(player)).toBe(11); // 6+2+3(maxHeight)
    });

    it('should subtract tearDown penalty', () => {
      const player = createMockPlayer('0', {
        sand: [10, 5]
      }, 3);
      expect(calculatePlayerScore(player)).toBe(-2); // 2+2(maxHeight)-6(penalty)
    });
  });

  describe('calculateTearDownPenalty', () => {
    it('should return 0 for no tearDown cards', () => {
      expect(calculateTearDownPenalty(0)).toBe(0);
    });

    it('should calculate triangular number for 1 card', () => {
      expect(calculateTearDownPenalty(1)).toBe(1); // 1
    });

    it('should calculate triangular number for 2 cards', () => {
      expect(calculateTearDownPenalty(2)).toBe(3); // 1+2
    });

    it('should calculate triangular number for 3 cards', () => {
      expect(calculateTearDownPenalty(3)).toBe(6); // 1+2+3
    });

    it('should calculate triangular number for 5 cards', () => {
      expect(calculateTearDownPenalty(5)).toBe(15); // 1+2+3+4+5
    });

    it('should calculate triangular number for 10 cards', () => {
      expect(calculateTearDownPenalty(10)).toBe(55); // 10*11/2
    });
  });

  describe('getScoreRankings', () => {
    it('should rank single player', () => {
      const players = [createMockPlayer('0', {}, 0)];
      const rankings = getScoreRankings(players);
      expect(rankings.length).toBe(1);
      expect(rankings[0].rank).toBe(1);
    });

    it('should rank players by score descending', () => {
      const players = [
        createMockPlayer('0', { sand: [10, 5, 3] }, 0), // Score: 6 (3+3)
        createMockPlayer('1', { sand: [15, 10] }, 0),   // Score: 4 (2+2)
        createMockPlayer('2', { sand: [12, 8, 4, 2] }, 0) // Score: 8 (4+4)
      ];
      const rankings = getScoreRankings(players);
      expect(rankings[0].rank).toBe(1);
      expect(rankings[0].player.id).toBe('2');
      expect(rankings[1].rank).toBe(2);
      expect(rankings[1].player.id).toBe('0');
      expect(rankings[2].rank).toBe(3);
      expect(rankings[2].player.id).toBe('1');
    });

    it('should handle tied scores', () => {
      const players = [
        createMockPlayer('0', { sand: [10, 5] }, 0), // Score: 3
        createMockPlayer('1', { sand: [15, 10] }, 0)  // Score: 3
      ];
      const rankings = getScoreRankings(players);
      expect(rankings.length).toBe(2);
      // Both should have rank 1 or 2 depending on sort stability
      expect([1, 2]).toContain(rankings[0].rank);
      expect([1, 2]).toContain(rankings[1].rank);
    });
  });
});
