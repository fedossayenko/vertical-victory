// Enums
export enum TowerSuit {
  SAND = "sand",
  STONE = "stone",
  VEGETATION = "vegetation",
  WATER = "water",
  FIRE = "fire"
}

export enum GamePhase {
  LOBBY = "lobby",
  BIDDING = "bidding",
  BUILDING = "building",
  SCORING = "scoring",
  GAME_OVER = "game_over"
}

// Core interfaces
export interface Card {
  id: string;
  suit: TowerSuit;
  value: number;
  readonly isTowerTop: boolean;
  readonly isReset: boolean;
  readonly isWild: boolean;
}

export interface Tower {
  suit: TowerSuit;
  cards: readonly Card[];
  readonly height: number;
  readonly isCapped: boolean;
}

export interface PlayerState {
  id: string;
  name: string;
  towers: Record<TowerSuit, Tower>;
  hand: readonly Card[];
  tearDownPile: readonly Card[];
  currentBid: number | null;
  hasPassed: boolean;
  readonly totalScore: number;
}

export interface GameState {
  players: PlayerState[];
  currentPlayerIndex: number;
  phase: GamePhase;
  displayCards: readonly Card[];
  deck: readonly Card[];
  discardPile: readonly Card[];
  currentHighBid: number;
  highBidderIndex: number | null;
  auctionWinnerIndex: number | null;
  cardsToProcess: readonly Card[];
  roundNumber: number;
}
