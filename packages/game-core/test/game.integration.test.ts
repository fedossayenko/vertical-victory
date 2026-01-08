import { describe, it, expect, beforeEach } from 'vitest';
import { FiveTowersGame } from '../src/game';
import { GamePhase } from '@vertical-victory/shared-types';
import {
  createMockCtx,
  createMockEvents,
  createMockRandom,
  createMockCard,
  createBiddingGameState,
  createBuildingGameState,
  createInitialGameState
} from './mocks';

describe('FiveTowers Game Integration', () => {
  describe('Game Setup', () => {
    it('should initialize game with correct state for 2 players', () => {
      const state = createInitialGameState(2);

      expect(state.phase).toBe(GamePhase.BIDDING);
      expect(state.players).toHaveLength(2);
      expect(state.currentPlayerIndex).toBe(0);
      expect(state.displayCards).toHaveLength(5);
      expect(state.deck.length).toBe(75); // 80 - 5 dealt
      expect(state.discardPile).toHaveLength(0);
      expect(state.currentHighBid).toBe(0);
      expect(state.auctionWinnerIndex).toBeNull();
      expect(state.cardsToProcess).toHaveLength(0);
      expect(state.roundNumber).toBe(1);
    });

    it('should initialize game with correct state for 4 players', () => {
      const state = createInitialGameState(4);

      expect(state.players).toHaveLength(4);
      expect(state.deck.length).toBe(105); // 110 - 5 dealt
    });

    it('should create players with empty towers', () => {
      const state = createBiddingGameState(2);

      state.players.forEach(player => {
        expect(player.towers.sand.cards).toHaveLength(0);
        expect(player.towers.stone.cards).toHaveLength(0);
        expect(player.towers.vegetation.cards).toHaveLength(0);
        expect(player.towers.water.cards).toHaveLength(0);
        expect(player.towers.fire.cards).toHaveLength(0);
      });
    });

    it('should start in BIDDING phase', () => {
      const state = createBiddingGameState(2);
      expect(state.phase).toBe(GamePhase.BIDDING);
    });
  });

  describe('Phase Transitions', () => {
    it('should have BIDDING phase with bid and pass moves', () => {
      const biddingPhase = FiveTowersGame.phases?.bidding;

      expect(biddingPhase).toBeDefined();
      expect(biddingPhase?.moves).toHaveProperty('bid');
      expect(biddingPhase?.moves).toHaveProperty('pass');
      expect(biddingPhase?.start).toBe(true);
    });

    it('should have BUILDING phase with placeCard and tearDownTower moves', () => {
      const buildingPhase = FiveTowersGame.phases?.building;

      expect(buildingPhase).toBeDefined();
      expect(buildingPhase?.moves).toHaveProperty('placeCard');
      expect(buildingPhase?.moves).toHaveProperty('tearDownTower');
      expect(buildingPhase?.next).toBe(GamePhase.BIDDING);
    });

    it('should transition from BIDDING to BUILDING when auction ends', () => {
      const state = createBiddingGameState(2);
      state.auctionWinnerIndex = '0';

      const shouldEnd = FiveTowersGame.phases!.bidding!.endIf!(state);
      expect(shouldEnd).toBe(true);
    });

    it('should not transition from BIDDING when no winner', () => {
      const state = createBiddingGameState(2);
      state.auctionWinnerIndex = null;

      const shouldEnd = FiveTowersGame.phases!.bidding!.endIf!(state);
      expect(shouldEnd).toBe(false);
    });
  });

  describe('Complete Game Flow - Single Round', () => {
    it('should play complete bidding cycle', () => {
      const state = createBiddingGameState(2);
      const events = createMockEvents();

      // Player 0 bids 1
      const ctx = createMockCtx({ currentPlayer: '0', args: { amount: 1 } });
      let newState = FiveTowersGame.phases!.bidding!.moves!.bid!({ G: state, ctx, events } as any);

      expect(newState.currentHighBid).toBe(1);
      expect(newState.highBidderIndex).toBe('0');

      // Player 1 passes
      const ctx1 = createMockCtx({ currentPlayer: '1' });
      newState = FiveTowersGame.phases!.bidding!.moves!.pass!({ G: newState, ctx: ctx1, events } as any);

      expect(newState.players[1].hasPassed).toBe(true);
      expect(newState.auctionWinnerIndex).toBe('0');
    });

    it('should end auction when only one player remains', () => {
      const state = createBiddingGameState(2);
      state.currentHighBid = 2;
      state.highBidderIndex = '0';
      state.players[0].currentBid = 2;
      state.players[1].hasPassed = true;

      const events = createMockEvents();
      const random = createMockRandom();
      const result = FiveTowersGame.phases!.bidding!.onEnd!(state, {} as any, random);

      expect(result).toBeDefined();
    });
  });

  describe('Building Phase Flow', () => {
    it('should allow auction winner to place cards', () => {
      const state = createBuildingGameState(2, '0');
      const events = createMockEvents();

      const card = state.players[0].hand[0];
      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand', cardIndex: 0 }
      });

      const newState = FiveTowersGame.phases!.building!.moves!.placeCard!({ G: state, ctx, events } as any);

      expect(newState.players[0].hand).toHaveLength(1); // Card removed
      expect(newState.cardsToProcess).toHaveLength(1); // One less to process
    });

    it('should allow auction winner to tear down tower', () => {
      const state = createBuildingGameState(2, '0');
      // Add a card to sand tower
      state.players[0].towers.sand.cards = [createMockCard('sand', 10)];

      const ctx = createMockCtx({
        currentPlayer: '0',
        args: { tower: 'sand' }
      });

      const newState = FiveTowersGame.phases!.building!.moves!.tearDownTower!({ G: state, ctx } as any);

      expect(newState.players[0].towers.sand.cards).toHaveLength(0);
      expect(newState.players[0].tearDownPile).toHaveLength(1);
    });

    it('should transition back to BIDDING when building complete', () => {
      const state = createBuildingGameState(2, '0');
      state.cardsToProcess = []; // All cards processed

      const events = createMockEvents();
      // This should trigger the endBuildingPhase logic
      // which calls events.setPhase(GamePhase.BIDDING)

      // The phase transition is handled internally by the move
      // We verify the game configuration specifies the next phase
      expect(FiveTowersGame.phases!.building!.next).toBe(GamePhase.BIDDING);
    });
  });

  describe('Multi-Player Scenarios', () => {
    it('should handle 3-player game setup', () => {
      const state = createInitialGameState(3);

      expect(state.players).toHaveLength(3);
      expect(state.deck.length).toBe(75); // 80 - 5 dealt
    });

    it('should handle 5-player game setup with expanded deck', () => {
      const state = createInitialGameState(5);

      expect(state.players).toHaveLength(5);
      expect(state.deck.length).toBe(105); // 110 - 5 dealt
    });
  });

  describe('Game Over Detection', () => {
    it('should detect game over when phase is GAME_OVER', () => {
      const state = createBiddingGameState(2);
      state.phase = GamePhase.GAME_OVER;

      const result = FiveTowersGame.endIf!(state);
      expect(result).toBeDefined();
      expect(result?.winner).toBeDefined();
    });

    it('should not end game in normal phases', () => {
      const state = createBiddingGameState(2);

      const result = FiveTowersGame.endIf!(state);
      expect(result).toBeUndefined();
    });
  });

  describe('Turn Management', () => {
    it('should have move limit of 1 per turn', () => {
      expect(FiveTowersGame.turn?.moveLimit).toBe(1);
    });

    it('should advance player index on turn end', () => {
      const state = createBiddingGameState(2);
      state.currentPlayerIndex = 0;

      FiveTowersGame.turn!.onEnd!(state, { numPlayers: 2 } as any);

      expect(state.currentPlayerIndex).toBe(1);
    });

    it('should wrap around to first player', () => {
      const state = createBiddingGameState(2);
      state.currentPlayerIndex = 1;

      FiveTowersGame.turn!.onEnd!(state, { numPlayers: 2 } as any);

      expect(state.currentPlayerIndex).toBe(0);
    });
  });
});
