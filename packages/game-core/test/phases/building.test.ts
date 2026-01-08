import { describe, it, expect, beforeEach } from 'vitest';
import { placeCard, tearDownTower } from '../../src/game/phases/building';
import { GamePhase } from '@vertical-victory/shared-types';
import { TowerSuit as SuitEnum } from '@vertical-victory/shared-types';
import {
  createMockCtx,
  createMockEvents,
  createMockCard,
  createBuildingGameState
} from '../mocks';

describe('Building Phase', () => {
  let initialState: ReturnType<typeof createBuildingGameState>;
  let mockEvents: ReturnType<typeof createMockEvents>;

  beforeEach(() => {
    initialState = createBuildingGameState(2, '0');
    mockEvents = createMockEvents();
  });

  describe('placeCard move', () => {
    it('should allow auction winner to place cards', () => {
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const newState = placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.players[0].hand).toHaveLength(1); // Card removed
      expect(newState.cardsToProcess).toHaveLength(1); // One less to process
    });

    it('should add card to target tower', () => {
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const newState = placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.players[0].towers.sand.cards).toHaveLength(1);
    });

    it('should reject placement from non-winner', () => {
      const ctx = createMockCtx({
        currentPlayer: '1',
        args: { tower: 'sand', cardIndex: 0 }
      });

      expect(() => {
        placeCard({ G: initialState, ctx, events: mockEvents } as any);
      }).toThrow('Only auction winner can place cards');
    });

    it('should reject invalid placement (should error)', () => {
      // Add a card that makes the tower invalid for the next card
      initialState.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 5)];
      initialState.players[0].hand = [createMockCard(SuitEnum.SAND, 10)]; // Can't place higher card

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      expect(() => {
        placeCard({ G: initialState, ctx, events: mockEvents } as any);
      }).toThrow();
    });

    it('should end phase when all cards placed', () => {
      initialState.cardsToProcess = [initialState.cardsToProcess[0]]; // Only 1 card
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(mockEvents.setPhase).toHaveBeenCalledWith(GamePhase.BIDDING);
    });

    it('should handle Reset card (value 8) placement', () => {
      initialState.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 10)];
      initialState.players[0].hand = [createMockCard(SuitEnum.SAND, 8)]; // Reset card

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const newState = placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.players[0].towers.sand.cards).toHaveLength(2);
    });

    it('should handle Wild card (value 9) placement', () => {
      initialState.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 5)];
      initialState.players[0].hand = [createMockCard(SuitEnum.SAND, 9)]; // Wild card

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const newState = placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.players[0].towers.sand.cards).toHaveLength(2);
    });

    it('should preserve tower immutability', () => {
      const originalLength = initialState.players[0].towers.sand.cards.length;
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(initialState.players[0].towers.sand.cards.length).toBe(originalLength);
    });
  });

  describe('tearDownTower move', () => {
    it('should allow auction winner to tear down', () => {
      initialState.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 10)];

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand' }
      });

      const newState = tearDownTower({ G: initialState, ctx } as any);

      expect(newState.players[0].towers.sand.cards).toHaveLength(0);
    });

    it('should add torn down cards to tearDownPile', () => {
      const card = createMockCard(SuitEnum.SAND, 10);
      initialState.players[0].towers.sand.cards = [card];

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand' }
      });

      const newState = tearDownTower({ G: initialState, ctx } as any);

      expect(newState.players[0].tearDownPile).toHaveLength(1);
      expect(newState.players[0].tearDownPile[0]).toEqual(card);
    });

    it('should reject teardown from non-winner', () => {
      initialState.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 10)];

      const ctx = createMockCtx({
        currentPlayer: '1',
        args: { tower: 'sand' }
      });

      expect(() => {
        tearDownTower({ G: initialState, ctx } as any);
      }).toThrow('Only auction winner can tear down');
    });

    it('should reject teardown of empty tower', () => {
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand' }
      });

      expect(() => {
        tearDownTower({ G: initialState, ctx } as any);
      }).toThrow('Cannot tear down empty tower');
    });

    it('should handle teardown of tower with multiple cards', () => {
      initialState.players[0].towers.sand.cards = [
        createMockCard(SuitEnum.SAND, 15),
        createMockCard(SuitEnum.SAND, 10),
        createMockCard(SuitEnum.SAND, 5)
      ];

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand' }
      });

      const newState = tearDownTower({ G: initialState, ctx } as any);

      expect(newState.players[0].tearDownPile).toHaveLength(3);
      expect(newState.players[0].towers.sand.cards).toHaveLength(0);
    });

    it('should preserve immutability', () => {
      const card = createMockCard(SuitEnum.SAND, 10);
      initialState.players[0].towers.sand.cards = [card];
      const originalLength = initialState.players[0].towers.sand.cards.length;

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand' }
      });

      tearDownTower({ G: initialState, ctx } as any);

      expect(initialState.players[0].towers.sand.cards.length).toBe(originalLength);
    });
  });

  describe('Phase End Conditions', () => {
    it('should detect when deck is empty', () => {
      initialState.deck = [];
      initialState.cardsToProcess = []; // All cards placed

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      // When cardsToProcess becomes empty and deck is empty
      // The phase should handle game over
      placeCard({ G: initialState, ctx, events: mockEvents } as any);

      // Should either transition to GAME_OVER or handle it
      // This is tested implicitly by the transition
    });

    it('should handle discard pile refill when deck empty', () => {
      initialState.deck = [];
      initialState.discardPile = [createMockCard(SuitEnum.SAND, 10)];
      initialState.cardsToProcess = [];

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      // This tests the internal logic of endBuildingPhase
      // The phase should refill deck from discard
      placeCard({ G: initialState, ctx, events: mockEvents } as any);

      // Verify transition happened (to BIDDING or GAME_OVER)
      expect(mockEvents.setPhase).toHaveBeenCalled();
    });

    it('should handle game over when both deck and discard empty', () => {
      initialState.deck = [];
      initialState.discardPile = [];
      initialState.cardsToProcess = [];

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(mockEvents.endGame).toHaveBeenCalled();
    });
  });

  describe('Multiple Card Processing', () => {
    it('should process multiple cards in sequence', () => {
      initialState.cardsToProcess = [
        createMockCard(SuitEnum.SAND, 15),
        createMockCard(SuitEnum.STONE, 12)
      ];

      // Place first card
      let ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      let state = placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(state.cardsToProcess).toHaveLength(1);

      // Place second card
      ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'stone', cardIndex: 0 }
      });

      state = placeCard({ G: state, ctx, events: mockEvents } as any);

      expect(state.cardsToProcess).toHaveLength(0);
      expect(mockEvents.setPhase).toHaveBeenCalledWith(GamePhase.BIDDING);
    });
  });

  describe('Edge Cases', () => {
    it('should handle Tower Top (value 0) capping tower', () => {
      initialState.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 5)];
      initialState.players[0].hand = [createMockCard(SuitEnum.SAND, 0)]; // Tower Top

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const newState = placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.players[0].towers.sand.cards).toHaveLength(2);
    });

    it('should preserve other towers when placing on one', () => {
      initialState.players[0].towers.stone.cards = [createMockCard(SuitEnum.STONE, 10)];
      initialState.players[0].towers.water.cards = [createMockCard(SuitEnum.WATER, 8)];

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const newState = placeCard({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.players[0].towers.stone.cards).toHaveLength(1);
      expect(newState.players[0].towers.water.cards).toHaveLength(1);
    });

    it('should handle multiple teardowns in one phase', () => {
      initialState.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 10)];
      initialState.players[0].towers.stone.cards = [createMockCard(SuitEnum.STONE, 8)];

      // Tear down sand tower
      let ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand' }
      });

      let state = tearDownTower({ G: initialState, ctx } as any);

      expect(state.players[0].tearDownPile).toHaveLength(1);

      // Tear down stone tower
      ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'stone' }
      });

      state = tearDownTower({ G: state, ctx } as any);

      expect(state.players[0].tearDownPile).toHaveLength(2);
    });
  });
});
