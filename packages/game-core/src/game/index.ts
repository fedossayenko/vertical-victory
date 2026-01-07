import type { Game } from 'boardgame.io';
import type { GameState, GamePhase, TowerSuit } from '@vertical-victory/shared-types';
import { TowerSuit as SuitEnum, GamePhase as PhaseEnum } from '@vertical-victory/shared-types';
import { createStandardDeck, shuffleDeck, dealDisplayCards } from '../logic/deck';
import { bid, pass, endAuction } from './phases/bidding';
import { placeCard, tearDownTower } from './phases/building';
import { produce } from 'immer';

export const FiveTowersGame: Game<GameState> = {
  name: 'five-towers',

  setup: ({ ctx, random }) => {
    // Create deck
    const deck = createStandardDeck(ctx.numPlayers);
    const shuffledDeck = shuffleDeck(deck, random);

    // Deal initial display cards
    const { deck: remainingDeck, cards } = dealDisplayCards(shuffledDeck, 5);

    // Initialize players
    const players = Array.from({ length: ctx.numPlayers }, (_, i) => ({
      id: String(i),
      name: `Player ${i + 1}`,
      towers: {
        sand: { suit: 'sand', cards: [], height: 0, isCapped: false },
        stone: { suit: 'stone', cards: [], height: 0, isCapped: false },
        vegetation: { suit: 'vegetation', cards: [], height: 0, isCapped: false },
        water: { suit: 'water', cards: [], height: 0, isCapped: false },
        fire: { suit: 'fire', cards: [], height: 0, isCapped: false }
      },
      hand: [],
      tearDownPile: [],
      currentBid: null,
      hasPassed: false,
      totalScore: 0
    }));

    return {
      players,
      currentPlayerIndex: 0,
      phase: PhaseEnum.BIDDING,
      displayCards: cards,
      deck: remainingDeck,
      discardPile: [],
      currentHighBid: 0,
      highBidderIndex: null,
      auctionWinnerIndex: null,
      cardsToProcess: [],
      roundNumber: 1
    };
  },

  phases: {
    bidding: {
      start: true,
      moves: { bid, pass },
      turn: {
        order: {
          first: () => 0,
          next: (G, ctx) => (G.currentPlayerIndex + 1) % ctx.numPlayers
        }
      },
      endIf: (G) => G.auctionWinnerIndex !== null,
      next: PhaseEnum.BUILDING,
      onEnd: (G, ctx, random) => {
        return endAuction(G, random);
      }
    },
    building: {
      moves: { placeCard, tearDownTower },
      next: PhaseEnum.BIDDING
    }
  },

  turn: {
    moveLimit: 1,
    onEnd: (G, ctx) => {
      // Advance turn
      G.currentPlayerIndex = (G.currentPlayerIndex + 1) % ctx.numPlayers;
    }
  },

  endIf: (G) => {
    return G.phase === PhaseEnum.GAME_OVER ? { winner: getWinner(G) } : undefined;
  }
};

function getWinner(G: GameState): string {
  // Calculate scores and find winner
  let winner = G.players[0].id;
  let highestScore = 0;

  for (const player of G.players) {
    const score = player.totalScore;
    if (score > highestScore) {
      highestScore = score;
      winner = player.id;
    }
  }

  return winner;
}
