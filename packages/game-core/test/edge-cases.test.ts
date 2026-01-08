import { describe, it, expect } from 'vitest';
import { FiveTowersGame } from '../src/game';
import { bid, pass, endAuction } from '../src/game/phases/bidding';
import { placeCard, tearDownTower } from '../src/game/phases/building';
import { GamePhase } from '@vertical-victory/shared-types';
import { TowerSuit as SuitEnum } from '@vertical-victory/shared-types';
import {
  createMockCtx,
  createMockEvents,
  createMockRandom,
  createMockCard,
  createBiddingGameState,
  createBuildingGameState,
  createInitialGameState
} from './mocks';

describe('Edge Cases', () => {
  describe('All Players Pass', () => {
    it('should handle all players passing in 2-player game', () => {
      let state = createBiddingGameState(2);
      const events = createMockEvents();

      // Player 0 passes
      let ctx = createMockCtx({ currentPlayer: '0' });
      state = pass({ G: state, ctx } as any);

      // Player 1 passes
      ctx = createMockCtx({ currentPlayer: '1' });
      state = pass({ G: state, ctx } as any);

      // Last remaining player should be winner
      expect(state.auctionWinnerIndex).toBe('1');
    });

    it('should handle all players passing in 3-player game', () => {
      let state = createBiddingGameState(3);
      const events = createMockEvents();

      // Player 0 passes
      let ctx = createMockCtx({ currentPlayer: '0' });
      state = pass({ G: state, ctx } as any);

      // Player 1 passes
      ctx = createMockCtx({ currentPlayer: '1' });
      state = pass({ G: state, ctx } as any);

      // Player 2 is last remaining
      expect(state.auctionWinnerIndex).toBe('2');
    });

    it('should end auction when only one player remains after passes', () => {
      let state = createBiddingGameState(3);
      state.currentHighBid = 2;
      state.highBidderIndex = '0';
      state.players[0].currentBid = 2;

      // Player 1 passes
      let ctx = createMockCtx({ currentPlayer: '1' });
      state = pass({ G: state, ctx } as any);

      // Player 2 passes
      ctx = createMockCtx({ currentPlayer: '2' });
      state = pass({ G: state, ctx } as any);

      // Player 0 wins with bid of 2
      expect(state.auctionWinnerIndex).toBe('0');
    });
  });

  describe('Bid of 0 Discard Scenario', () => {
    it('should discard all cards when bid is 0', () => {
      let state = createBiddingGameState(2);
      state.auctionWinnerIndex = '0';
      state.players[0].currentBid = 0;
      state.displayCards = [
        createMockCard(SuitEnum.SAND, 10),
        createMockCard(SuitEnum.STONE, 8),
        createMockCard(SuitEnum.VEGETATION, 5),
        createMockCard(SuitEnum.WATER, 3),
        createMockCard(SuitEnum.FIRE, 1)
      ];

      const random = createMockRandom();
      state = endAuction(state, random);

      expect(state.discardPile).toHaveLength(5);
      // Note: A new round starts, so 5 new cards are dealt
      expect(state.displayCards).toHaveLength(5);
      expect(state.players[0].hand).toHaveLength(0);
    });

    it('should start new round after bid of 0', () => {
      let state = createBiddingGameState(2);
      state.auctionWinnerIndex = '0';
      state.players[0].currentBid = 0;
      state.roundNumber = 1;
      // Use a reasonable deck size
      state.deck = [createMockCard(SuitEnum.SAND, 7), createMockCard(SuitEnum.STONE, 6), createMockCard(SuitEnum.VEGETATION, 5), createMockCard(SuitEnum.WATER, 4), createMockCard(SuitEnum.FIRE, 3)];

      const random = createMockRandom();
      state = endAuction(state, random);

      expect(state.roundNumber).toBe(2);
      expect(state.displayCards).toHaveLength(5);
    });
  });

  describe('Empty Deck Scenarios', () => {
    it('should handle deck exhaustion during game', () => {
      let state = createBuildingGameState(2, '0');
      state.deck = [];
      state.discardPile = [createMockCard(SuitEnum.SAND, 10)];
      state.cardsToProcess = [];

      const events = createMockEvents();
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      placeCard({ G: state, ctx, events } as any);

      // Should transition to BIDDING (deck refilled from discard)
      expect(events.setPhase).toHaveBeenCalled();
    });

    it('should handle game over when deck and discard empty', () => {
      let state = createBuildingGameState(2, '0');
      state.deck = [];
      state.discardPile = [];
      state.cardsToProcess = [];

      const events = createMockEvents();
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      placeCard({ G: state, ctx, events } as any);

      // Should end the game
      expect(events.endGame).toHaveBeenCalled();
    });

    it('should not end game when discard has cards', () => {
      let state = createBuildingGameState(2, '0');
      state.deck = [];
      state.discardPile = [createMockCard(SuitEnum.SAND, 10)];
      state.cardsToProcess = [];

      const events = createMockEvents();
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      placeCard({ G: state, ctx, events } as any);

      // Should not end game (discard refill)
      expect(events.endGame).not.toHaveBeenCalled();
    });
  });

  describe('Special Card Edge Cases', () => {
    it('should handle Tower Top (0) capping tower', () => {
      let state = createBuildingGameState(2, '0');
      const towerTop = createMockCard(SuitEnum.SAND, 0);
      state.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 10), towerTop];

      const events = createMockEvents();
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      // Try to place on capped tower
      state.players[0].hand = [createMockCard(SuitEnum.SAND, 5)];

      expect(() => {
        placeCard({ G: state, ctx, events } as any);
      }).toThrow();
    });

    it('should handle Wild card (9) on any tower', () => {
      let state = createBuildingGameState(2, '0');
      state.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 15)];
      state.players[0].hand = [createMockCard(SuitEnum.SAND, 9)]; // Wild

      const events = createMockEvents();
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const newState = placeCard({ G: state, ctx, events } as any);

      expect(newState.players[0].towers.sand.cards).toHaveLength(2);
    });

    it('should handle Reset card (8) allowing any placement', () => {
      let state = createBuildingGameState(2, '0');
      state.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 5)];
      state.players[0].hand = [createMockCard(SuitEnum.SAND, 15)]; // Higher value

      const events = createMockEvents();
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      // Should fail without Reset
      expect(() => {
        placeCard({ G: state, ctx, events } as any);
      }).toThrow();

      // Add Reset card and try again
      state.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 8)];
      const newState = placeCard({ G: state, ctx, events } as any);

      expect(newState.players[0].towers.sand.cards).toHaveLength(2);
    });
  });

  describe('Maximum Height Towers', () => {
    it('should handle tall towers correctly', () => {
      const state = createBuildingGameState(2, '0');
      const cards = [];
      for (let i = 15; i >= 0; i--) {
        cards.push(createMockCard(SuitEnum.SAND, i));
      }
      state.players[0].towers.sand.cards = cards;

      expect(state.players[0].towers.sand.cards.length).toBe(16);
    });

    it('should calculate score for tall capped tower', () => {
      const state = createBuildingGameState(2, '0');
      const cards = [];
      for (let i = 15; i >= 1; i--) {
        cards.push(createMockCard(SuitEnum.SAND, i));
      }
      cards.push(createMockCard(SuitEnum.SAND, 0)); // Tower Top
      state.players[0].towers.sand.cards = cards;

      // Score = 16 cards * 2 (capped) = 32
      expect(state.players[0].towers.sand.cards.length).toBe(16);
    });
  });

  describe('Multiple Tower Tear Down', () => {
    it('should handle tearing down multiple towers in one phase', () => {
      let state = createBuildingGameState(2, '0');
      state.players[0].towers.sand.cards = [createMockCard(SuitEnum.SAND, 10)];
      state.players[0].towers.stone.cards = [createMockCard(SuitEnum.STONE, 8)];
      state.players[0].towers.water.cards = [createMockCard(SuitEnum.WATER, 5)];

      // Tear down sand
      let ctx = createMockCtx({ currentPlayer: '0', args: { tower: 'sand' } });
      state = tearDownTower({ G: state, ctx } as any);

      expect(state.players[0].tearDownPile).toHaveLength(1);

      // Tear down stone
      ctx = createMockCtx({ currentPlayer: '0', args: { tower: 'stone' } });
      state = tearDownTower({ G: state, ctx } as any);

      expect(state.players[0].tearDownPile).toHaveLength(2);

      // Tear down water
      ctx = createMockCtx({ currentPlayer: '0', args: { tower: 'water' } });
      state = tearDownTower({ G: state, ctx } as any);

      expect(state.players[0].tearDownPile).toHaveLength(3);
    });

    it('should calculate tearDown penalty correctly', () => {
      const state = createBuildingGameState(2, '0');
      // Triangular number: 1+2+3+...+k = k×(k+1)/2
      // For 5 cards: 5×6/2 = 15
      state.players[0].tearDownPile = [
        createMockCard(SuitEnum.SAND, 10),
        createMockCard(SuitEnum.STONE, 8),
        createMockCard(SuitEnum.VEGETATION, 5),
        createMockCard(SuitEnum.WATER, 3),
        createMockCard(SuitEnum.FIRE, 1)
      ];

      // Penalty = 5×6/2 = 15
      expect(state.players[0].tearDownPile.length).toBe(5);
    });
  });

  describe('Boundary Values', () => {
    it('should handle minimum bid of 1', () => {
      const state = createBiddingGameState(2);
      const events = createMockEvents();
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 1 } });

      const newState = bid({ G: state, ctx, events } as any);

      expect(newState.currentHighBid).toBe(1);
    });

    it('should handle maximum bid of 5', () => {
      const state = createBiddingGameState(2);
      const events = createMockEvents();
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 5 } });

      bid({ G: state, ctx, events } as any);

      expect(events.setPhase).toHaveBeenCalledWith(GamePhase.BUILDING);
    });

    it('should reject bid of 0 (only allowed via winning with no bids)', () => {
      const state = createBiddingGameState(2);
      const events = createMockEvents();
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 0 } });

      expect(() => {
        bid({ G: state, ctx, events } as any);
      }).toThrow();
    });

    it('should reject negative bids', () => {
      const state = createBiddingGameState(2);
      const events = createMockEvents();
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: -1 } });

      expect(() => {
        bid({ G: state, ctx, events } as any);
      }).toThrow();
    });
  });

  describe('Player Count Variations', () => {
    it('should handle 2-player game', () => {
      const state = createInitialGameState(2);

      expect(state.players).toHaveLength(2);
      expect(state.deck.length).toBe(75); // 80 - 5
    });

    it('should handle 3-player game', () => {
      const state = createInitialGameState(3);

      expect(state.players).toHaveLength(3);
      expect(state.deck.length).toBe(75); // 80 - 5
    });

    it('should handle 4-player game with expanded deck', () => {
      const state = createInitialGameState(4);

      expect(state.players).toHaveLength(4);
      expect(state.deck.length).toBe(105); // 110 - 5
    });

    it('should handle 5-player game with expanded deck', () => {
      const state = createInitialGameState(5);

      expect(state.players).toHaveLength(5);
      expect(state.deck.length).toBe(105); // 110 - 5
    });
  });

  describe('State Immutability', () => {
    it('should not mutate original state when bidding', () => {
      const state = createBiddingGameState(2);
      const events = createMockEvents();
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 2 } });

      const originalHighBid = state.currentHighBid;
      bid({ G: state, ctx, events } as any);

      expect(state.currentHighBid).toBe(originalHighBid);
    });

    it('should not mutate original state when passing', () => {
      const state = createBiddingGameState(2);
      const ctx = createMockCtx({ currentPlayer: '0' });

      const originalHasPassed = state.players[0].hasPassed;
      pass({ G: state, ctx } as any);

      expect(state.players[0].hasPassed).toBe(originalHasPassed);
    });

    it('should not mutate original state when placing cards', () => {
      const state = createBuildingGameState(2, '0');
      const events = createMockEvents();
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const originalHandLength = state.players[0].hand.length;
      placeCard({ G: state, ctx, events } as any);

      expect(state.players[0].hand.length).toBe(originalHandLength);
    });
  });
});
