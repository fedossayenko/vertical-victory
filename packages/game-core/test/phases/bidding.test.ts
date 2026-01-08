import { describe, it, expect, beforeEach } from 'vitest';
import { bid, pass, endAuction } from '../../src/game/phases/bidding';
import { GamePhase } from '@vertical-victory/shared-types';
import { TowerSuit as SuitEnum } from '@vertical-victory/shared-types';
import {
  createMockCtx,
  createMockEvents,
  createMockRandom,
  createMockCard,
  createBiddingGameState
} from '../mocks';

describe('Bidding Phase', () => {
  let initialState: ReturnType<typeof createBiddingGameState>;
  let mockEvents: ReturnType<typeof createMockEvents>;

  beforeEach(() => {
    initialState = createBiddingGameState(2);
    mockEvents = createMockEvents();
  });

  describe('bid move', () => {
    it('should accept valid bid (1-5)', () => {
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 2 } });
      const newState = bid({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.currentHighBid).toBe(2);
      expect(newState.highBidderIndex).toBe('0');
      expect(newState.players[0].currentBid).toBe(2);
    });

    it('should accept bid of 1 as minimum', () => {
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 1 } });
      const newState = bid({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.currentHighBid).toBe(1);
    });

    it('should accept bid of 5 as maximum', () => {
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 5 } });
      const newState = bid({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.currentHighBid).toBe(5);
    });

    it('should reject bid <= current high bid', () => {
      initialState.currentHighBid = 3;
      const ctx = createMockCtx({ currentPlayer: '1', args: { amount: 3 } });

      expect(() => {
        bid({ G: initialState, ctx, events: mockEvents } as any);
      }).toThrow('Bid must be higher than 3');
    });

    it('should reject bid lower than current high bid', () => {
      initialState.currentHighBid = 3;
      const ctx = createMockCtx({ currentPlayer: '1', args: { amount: 2 } });

      expect(() => {
        bid({ G: initialState, ctx, events: mockEvents } as any);
      }).toThrow('Bid must be higher than 3');
    });

    it('should reject bid > 5', () => {
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 6 } });

      expect(() => {
        bid({ G: initialState, ctx, events: mockEvents } as any);
      }).toThrow('Maximum bid is 5');
    });

    it('should reject bid from player who has passed', () => {
      initialState.players[0].hasPassed = true;
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 2 } });

      expect(() => {
        bid({ G: initialState, ctx, events: mockEvents } as any);
      }).toThrow('Player has already passed');
    });

    it('should end auction immediately on bid of 5', () => {
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 5 } });
      bid({ G: initialState, ctx, events: mockEvents } as any);

      expect(mockEvents.setPhase).toHaveBeenCalledWith(GamePhase.BUILDING);
    });

    it('should update auction winner on bid of 5', () => {
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 5 } });
      const newState = bid({ G: initialState, ctx, events: mockEvents } as any);

      expect(newState.auctionWinnerIndex).toBe('0');
    });

    it('should allow multiple players to bid in sequence', () => {
      let ctx = createMockCtx({ currentPlayer: '0', args: { amount: 2 } });
      let state = bid({ G: initialState, ctx, events: mockEvents } as any);

      ctx = createMockCtx({ currentPlayer: '1', args: { amount: 3 } });
      state = bid({ G: state, ctx, events: mockEvents } as any);

      expect(state.currentHighBid).toBe(3);
      expect(state.highBidderIndex).toBe('1');
    });
  });

  describe('pass move', () => {
    it('should mark player as passed', () => {
      const ctx = createMockCtx({ currentPlayer: '0' });
      const newState = pass({ G: initialState, ctx } as any);

      expect(newState.players[0].hasPassed).toBe(true);
    });

    it('should clear player bid when passing', () => {
      initialState.players[0].currentBid = 3;
      const ctx = createMockCtx({ currentPlayer: '0' });
      const newState = pass({ G: initialState, ctx } as any);

      expect(newState.players[0].currentBid).toBeNull();
    });

    it('should reject double pass', () => {
      initialState.players[0].hasPassed = true;
      const ctx = createMockCtx({ currentPlayer: '0' });

      expect(() => {
        pass({ G: initialState, ctx } as any);
      }).toThrow('Player has already passed');
    });

    it('should end auction when only one player remains', () => {
      // First, player 0 makes a bid
      let ctx = createMockCtx({ currentPlayer: '0', args: { amount: 2 } });
      let state = bid({ G: initialState, ctx, events: mockEvents } as any);

      // Then player 1 passes
      ctx = createMockCtx({ currentPlayer: '1' });
      state = pass({ G: state, ctx } as any);

      expect(state.auctionWinnerIndex).toBe('0');
    });

    it('should not end auction when multiple players remain', () => {
      // Use 3 players to test multiple remaining bidders
      let state = createBiddingGameState(3);

      // First, have player 1 make a bid so they're an active bidder
      let ctx = createMockCtx({ currentPlayer: '1', args: { amount: 2 } });
      state = bid({ G: state, ctx, events: mockEvents } as any);

      // Then player 0 passes - auction should not end since player 1 is still active
      ctx = createMockCtx({ currentPlayer: '0' });
      state = pass({ G: state, ctx } as any);

      expect(state.auctionWinnerIndex).toBeNull();
    });
  });

  describe('endAuction', () => {
    it('should return unchanged state if no winner', () => {
      initialState.auctionWinnerIndex = null;
      const random = createMockRandom();
      const newState = endAuction(initialState, random);

      expect(newState).toBe(initialState);
    });

    it('should discard all cards on bid of 0', () => {
      initialState.auctionWinnerIndex = '0';
      initialState.players[0].currentBid = 0;
      initialState.displayCards = [
        createMockCard(SuitEnum.SAND, 10),
        createMockCard(SuitEnum.STONE, 8)
      ];

      const random = createMockRandom();
      const newState = endAuction(initialState, random);

      expect(newState.discardPile).toHaveLength(2);
      // Note: A new round starts, so 5 new cards are dealt
      expect(newState.displayCards).toHaveLength(5);
    });

    it('should start new round after bid of 0', () => {
      initialState.auctionWinnerIndex = '0';
      initialState.players[0].currentBid = 0;
      initialState.roundNumber = 1;

      const random = createMockRandom();
      const newState = endAuction(initialState, random);

      expect(newState.roundNumber).toBe(2);
      expect(newState.displayCards).toHaveLength(5);
    });

    it('should award cards to winner based on bid', () => {
      initialState.auctionWinnerIndex = '0';
      initialState.players[0].currentBid = 2;
      initialState.displayCards = [
        createMockCard(SuitEnum.SAND, 10),
        createMockCard(SuitEnum.STONE, 8),
        createMockCard(SuitEnum.VEGETATION, 5),
        createMockCard(SuitEnum.WATER, 3),
        createMockCard(SuitEnum.FIRE, 1)
      ];

      const random = createMockRandom();
      const newState = endAuction(initialState, random);

      expect(newState.players[0].hand).toHaveLength(2);
      expect(newState.cardsToProcess).toHaveLength(2);
      expect(newState.discardPile).toHaveLength(3); // Remaining cards
    });

    it('should clear display cards after awarding', () => {
      initialState.auctionWinnerIndex = '0';
      initialState.players[0].currentBid = 3;
      initialState.displayCards = [
        createMockCard(SuitEnum.SAND, 10),
        createMockCard(SuitEnum.STONE, 8),
        createMockCard(SuitEnum.VEGETATION, 5),
        createMockCard(SuitEnum.WATER, 3),
        createMockCard(SuitEnum.FIRE, 1)
      ];

      const random = createMockRandom();
      const newState = endAuction(initialState, random);

      expect(newState.displayCards).toHaveLength(0);
    });

    it('should reset auction state for new round (bid of 0 only)', () => {
      initialState.auctionWinnerIndex = '0';
      initialState.players[0].currentBid = 0; // Bid of 0 triggers reset
      initialState.players[1].hasPassed = true;
      initialState.currentHighBid = 0;
      initialState.highBidderIndex = null;

      const random = createMockRandom();
      const newState = endAuction(initialState, random);

      expect(newState.currentHighBid).toBe(0);
      expect(newState.highBidderIndex).toBeNull();
      expect(newState.auctionWinnerIndex).toBeNull();
      expect(newState.players[0].currentBid).toBeNull();
      expect(newState.players[0].hasPassed).toBe(false);
      expect(newState.players[1].hasPassed).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    it('should handle all players passing immediately', () => {
      const ctx0 = createMockCtx({ currentPlayer: '0' });
      let state = pass({ G: initialState, ctx: ctx0 } as any);

      const ctx1 = createMockCtx({ currentPlayer: '1' });
      state = pass({ G: state, ctx: ctx1 } as any);

      expect(state.auctionWinnerIndex).toBe('1'); // Last remaining player
    });

    it('should handle bid of 5 winning with multiple players', () => {
      initialState.players[1].currentBid = 4;
      initialState.currentHighBid = 4;
      initialState.highBidderIndex = '1';

      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 5 } });
      bid({ G: initialState, ctx, events: mockEvents } as any);

      expect(mockEvents.setPhase).toHaveBeenCalledWith(GamePhase.BUILDING);
    });

    it('should preserve immutability of state', () => {
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 2 } });
      const originalHighBid = initialState.currentHighBid;

      bid({ G: initialState, ctx, events: mockEvents } as any);

      expect(initialState.currentHighBid).toBe(originalHighBid);
    });
  });
});
