import type { Move } from 'boardgame.io';
import type { GameState } from '@vertical-victory/shared-types';
import { GamePhase } from '@vertical-victory/shared-types';
import { produce } from 'immer';
import { dealDisplayCards } from '../../logic/deck';

export const bid: Move<GameState> = ({ G, ctx, events }) => {
  const amount = ctx.args?.amount as number;
  const playerID = ctx.currentPlayer;

  // Validation: must be higher than current bid
  if (amount <= G.currentHighBid) {
    throw new Error(`Bid must be higher than ${G.currentHighBid}`);
  }

  // Validation: max bid is 5
  if (amount > 5) {
    throw new Error('Maximum bid is 5');
  }

  // Validation: player must not have passed
  const player = G.players[playerID];
  if (player.hasPassed) {
    throw new Error('Player has already passed');
  }

  // Update state
  return produce(G, draft => {
    draft.players[playerID].currentBid = amount;
    draft.currentHighBid = amount;
    draft.highBidderIndex = playerID;

    // Bid of 5 wins immediately
    if (amount === 5) {
      draft.auctionWinnerIndex = playerID;
      events.setPhase(GamePhase.BUILDING);
    }
  });
};

export const pass: Move<GameState> = ({ G, ctx }) => {
  const playerID = ctx.currentPlayer;

  // Validation: must not have passed already
  if (G.players[playerID].hasPassed) {
    throw new Error('Player has already passed');
  }

  // Update state
  return produce(G, draft => {
    draft.players[playerID].hasPassed = true;
    draft.players[playerID].currentBid = null;

    // Check if auction is over (only 1 player hasn't passed)
    const activeBidders = draft.players.filter(p => !p.hasPassed);
    if (activeBidders.length === 1) {
      draft.auctionWinnerIndex = Number(activeBidders[0].id);
    }
  });
};

export function endAuction(G: GameState, random: { Shuffle<T>(arr: T[]): T[] }): GameState {
  const winnerIndex = G.auctionWinnerIndex;
  if (winnerIndex === null) return G;

  const winner = G.players[winnerIndex];
  const winningBid = winner.currentBid || 0;

  // Bid of 0 means discard all
  if (winningBid === 0) {
    return produce(G, draft => {
      draft.discardPile = [...draft.discardPile, ...G.displayCards];
      draft.displayCards = [];
      startNewRound(draft, random);
    });
  }

  // Winner selects cards
  const selectedCards = G.displayCards.slice(0, winningBid);
  const remainingCards = G.displayCards.slice(winningBid);

  return produce(G, draft => {
    draft.players[winnerIndex].hand = [
      ...draft.players[winnerIndex].hand,
      ...selectedCards
    ];
    draft.cardsToProcess = selectedCards;
    draft.discardPile = [...draft.discardPile, ...remainingCards];
    draft.displayCards = [];
  });
}

function startNewRound(G: any, random: { Shuffle<T>(arr: T[]): T[] }): void {
  // Deal 5 new cards
  const { deck: newDeck, cards } = dealDisplayCards(G.deck, 5);

  // Reset auction state
  G.players.forEach((p: PlayerState) => {
    p.currentBid = null;
    p.hasPassed = false;
  });
  G.currentHighBid = 0;
  G.highBidderIndex = null;
  G.auctionWinnerIndex = null;
  G.roundNumber++;
  G.deck = newDeck;
  G.displayCards = cards;
}
