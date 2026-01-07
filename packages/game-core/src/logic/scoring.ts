import { PlayerState, TowerSuit } from '@vertical-victory/shared-types';
import { calculateTowerScore } from './towers';

export function calculatePlayerScore(player: PlayerState): number {
  // Tower scores
  let towerScores = 0;
  let maxHeight = 0;

  for (const tower of Object.values(player.towers)) {
    towerScores += calculateTowerScore(tower);
    maxHeight = Math.max(maxHeight, tower.cards.length);
  }

  const bonus = maxHeight;
  const penalty = calculateTearDownPenalty(player.tearDownPile.length);

  const score = towerScores + bonus - penalty;

  // Update player's totalScore field
  (player as any).totalScore = score;

  return score;
}

export function calculateTearDownPenalty(count: number): number {
  if (count <= 0) return 0;
  // Triangular number: 1+2+3+...+k = k×(k+1)/2
  return count * (count + 1) / 2;
}

export function getScoreRankings(players: PlayerState[]): Array<{player: PlayerState; rank: number}> {
  const rankings = players
    .map(p => ({ player: p, score: calculatePlayerScore(p) }))
    .sort((a, b) => b.score - a.score)
    .map((item, index) => ({ player: item.player, rank: index + 1 }));

  return rankings;
}
