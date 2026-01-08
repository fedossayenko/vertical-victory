import { vi } from 'vitest';
import type { GameState, PlayerState, Card, TowerSuit } from '@vertical-victory/shared-types';
import { TowerSuit as SuitEnum, GamePhase } from '@vertical-victory/shared-types';
import { FiveTowersGame } from '../src/game';

/**
 * Mock utilities for boardgame.io testing
 */

export interface MockContext {
  numPlayers: number;
  currentPlayer: string;
  args?: any;
}

export interface MockEvents {
  setPhase: ReturnType<typeof vi.fn>;
  endGame: ReturnType<typeof vi.fn>;
}

export interface MockRandom {
  Shuffle: ReturnType<typeof vi.fn>;
}

/**
 * Creates a mock boardgame.io context
 */
export function createMockCtx(overrides: Partial<MockContext> = {}): MockContext {
  return {
    numPlayers: 2,
    currentPlayer: '0',
    ...overrides
  };
}

/**
 * Creates mock boardgame.io events
 */
export function createMockEvents(): MockEvents {
  return {
    setPhase: vi.fn(),
    endGame: vi.fn()
  };
}

/**
 * Creates mock random object with seeded shuffle
 */
export function createMockRandom(seed: number = 42): MockRandom {
  let state = seed;
  return {
    Shuffle: vi.fn((arr: any[]) => {
      // Simple deterministic shuffle for testing
      const result = [...arr];
      for (let i = result.length - 1; i > 0; i--) {
        state = (state * 1103515245 + 12345) & 0x7fffffff;
        const j = state % (i + 1);
        [result[i], result[j]] = [result[j], result[i]];
      }
      return result;
    })
  };
}

/**
 * Creates a mock card with proper getters
 */
export function createMockCard(suit: TowerSuit, value: number): Card {
  return {
    id: `card-${suit}-${value}`,
    suit,
    value,
    get isTowerTop() { return this.value === 0; },
    get isReset() { return this.value === 8; },
    get isWild() { return this.value === 9; }
  };
}

/**
 * Creates a mock player state
 */
export function createMockPlayer(overrides: Partial<PlayerState> = {}): PlayerState {
  return {
    id: '0',
    name: 'Player 1',
    towers: {
      sand: { suit: SuitEnum.SAND, cards: [] },
      stone: { suit: SuitEnum.STONE, cards: [] },
      vegetation: { suit: SuitEnum.VEGETATION, cards: [] },
      water: { suit: SuitEnum.WATER, cards: [] },
      fire: { suit: SuitEnum.FIRE, cards: [] }
    },
    hand: [],
    tearDownPile: [],
    currentBid: null,
    hasPassed: false,
    totalScore: 0,
    ...overrides
  };
}

/**
 * Creates an initial game state using the actual game setup
 */
export function createInitialGameState(numPlayers: number = 2): GameState {
  const mockCtx = {
    ctx: { numPlayers },
    random: createMockRandom()
  };

  return FiveTowersGame.setup!(mockCtx as any);
}

/**
 * Creates a game state in bidding phase
 */
export function createBiddingGameState(numPlayers: number = 2): GameState {
  const state = createInitialGameState(numPlayers);
  state.phase = GamePhase.BIDDING;
  return state;
}

/**
 * Creates a game state in building phase with auction winner
 */
export function createBuildingGameState(numPlayers: number = 2, winnerId: string = '0'): GameState {
  const state = createInitialGameState(numPlayers);
  state.phase = GamePhase.BUILDING;
  state.auctionWinnerIndex = winnerId;
  state.currentHighBid = 2;
  state.highBidderIndex = winnerId;

  // Give winner 2 cards to process
  const card1 = createMockCard(SuitEnum.SAND, 10);
  const card2 = createMockCard(SuitEnum.STONE, 8);
  state.players[Number(winnerId)].hand = [card1, card2];
  state.cardsToProcess = [card1, card2];

  return state;
}

/**
 * Creates a game state in game over phase
 */
export function createGameOverGameState(numPlayers: number = 2): GameState {
  const state = createInitialGameState(numPlayers);
  state.phase = GamePhase.GAME_OVER;
  state.deck = [];
  state.discardPile = [];
  return state;
}
