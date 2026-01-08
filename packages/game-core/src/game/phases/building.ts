import type { Move } from 'boardgame.io';
import type { GameState, TowerSuit } from '@vertical-victory/shared-types';
import { GamePhase } from '@vertical-victory/shared-types';
import { canPlaceCard, addCard, tearDown } from '../../logic/towers';
import { produce, type WritableDraft } from 'immer';

export const placeCard: Move<GameState> = ({ G, ctx, events }) => {
  const { tower, cardIndex } = (ctx as any).args as { tower: TowerSuit; cardIndex: number };
  const playerID = ctx.currentPlayer;

  // Validation: only auction winner can build
  if (playerID !== G.auctionWinnerIndex) {
    throw new Error('Only auction winner can place cards');
  }

  const player = G.players[Number(playerID)];
  const card = player.hand[cardIndex];
  const targetTower = player.towers[tower];

  // Validation: card can be placed on tower
  if (!canPlaceCard(targetTower, card)) {
    throw new Error(`Cannot place ${card.value} on ${tower} tower`);
  }

  // Update state
  return produce(G, draft => {
    const newTower = addCard(targetTower, card);
    draft.players[Number(playerID)].towers[tower] = newTower;

    // Remove card from hand
    draft.players[Number(playerID)].hand = player.hand.filter((_: any, i: number) => i !== cardIndex);
    draft.cardsToProcess = draft.cardsToProcess.filter((_, i) => i !== cardIndex);

    // Check if building is complete
    if (draft.cardsToProcess.length === 0) {
      endBuildingPhase(draft, events);
    }
  });
};

export const tearDownTower: Move<GameState> = ({ G, ctx }) => {
  const { tower } = (ctx as any).args as { tower: TowerSuit };
  const playerID = ctx.currentPlayer;

  // Validation: only auction winner can tear down
  if (playerID !== G.auctionWinnerIndex) {
    throw new Error('Only auction winner can tear down');
  }

  const targetTower = G.players[Number(playerID)].towers[tower];

  // Validation: tower must have cards
  if (targetTower.cards.length === 0) {
    throw new Error('Cannot tear down empty tower');
  }

  // Update state
  return produce(G, draft => {
    const { tower: newTower, cards } = tearDown(targetTower);
    draft.players[Number(playerID)].towers[tower] = newTower;
    draft.players[Number(playerID)].tearDownPile = [
      ...draft.players[Number(playerID)].tearDownPile,
      ...cards
    ];
  });
};

function endBuildingPhase(G: WritableDraft<GameState>, events: { setPhase: (phase: GamePhase) => void; endGame: () => void }): void {
  // Check if deck is empty
  if (G.deck.length === 0) {
    // Try to refill from discard
    if (G.discardPile.length > 0) {
      // Reshuffle discard into deck
      G.deck = G.discardPile;
      G.discardPile = [];
    } else {
      // Game over
      G.phase = GamePhase.GAME_OVER;
      events.endGame();
      return;
    }
  }

  // Start new round
  events.setPhase(GamePhase.BIDDING);
  G.currentPlayerIndex = 0;
}
