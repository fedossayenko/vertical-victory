# VerticalVictory

A web-based digital adaptation of the "5 Towers" card game with Deep Reinforcement Learning AI research focus.

## Project Overview

**VerticalVictory** implements the auction-based card game "5 Towers" by Kasper Lapp with a focus on training PPO (Proximal Policy Optimization) agents to play the game strategically.

### Game Mechanics

- **Auction Phase**: Players bid 0-5 cards to take from the 5 face-up display cards
- **Building Phase**: Winner places cards in descending order on 5 towers (one per suit)
- **Special Cards**:
  - **0 (Tower Top)**: Doubles tower points but caps the tower
  - **8 (Reset)**: Accepts any card on top
  - **9 (Wild)**: Can be placed on any card
- **Scoring**: Tower cards + tallest tower bonus - tear-down penalty

## Project Structure

```
vertical-victory/
├── packages/
│   ├── game-core/          # JS game logic (boardgame.io) ✅ Phase 3
│   │   ├── src/
│   │   │   ├── game/       # Game definition, phases, moves
│   │   │   └── logic/      # Deck, towers, scoring utilities
│   │   └── test/           # Unit tests (40 tests, all passing)
│   └── shared-types/       # Shared TypeScript types ✅
├── apps/
│   ├── web-app/            # React + Vite frontend - TODO (Phase 4)
│   └── training/           # Python Gymnasium + SB3 ✅ Phase 1-2
├── models/                 # Trained ONNX models
└── README.md
```

## Quick Start

### TypeScript Game Core (Phase 3)

```bash
# Install pnpm (if needed)
npm install -g pnpm

# Install dependencies
pnpm install

# Run tests
cd packages/game-core
pnpm test

# Type checking
pnpm type-check
```

### Python Training Environment (Phase 1-2)

```bash
# Install Poetry (if needed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
cd apps/training
poetry install

# Run tests
poetry run pytest

# Train a PPO agent (coming soon)
poetry run python scripts/train_ppo.py
```

## Development Status

- [x] **Phase 1**: Python game logic implementation
- [x] **Phase 1**: Gymnasium environment
- [x] **Phase 1**: Unit tests
- [x] **Phase 2**: PPO training implementation
- [x] **Phase 2**: Action masking
- [x] **Phase 3**: JavaScript game logic (boardgame.io)
- [x] **Phase 3**: Shared TypeScript types
- [x] **Phase 3**: Comprehensive unit tests (40 tests)
- [ ] **Phase 3**: Integration tests (in progress)
- [ ] **Phase 4**: React UI
- [ ] **Phase 5**: ONNX model integration
- [ ] **Phase 6**: Browser AI inference

## Architecture

### Technology Stack

**TypeScript Game Core**:
- **boardgame.io** (v0.50.0): Multiplayer game framework
- **immer** (v10.0.0): Immutable state updates
- **vitest** (v2.0.0): Testing framework
- **typescript** (v5.6.0): Strict mode enabled

**Python Training**:
- **Gymnasium**: RL environment interface
- **Stable-Baselines3**: PPO implementation
- **PyTorch**: Neural network training

### Key Design Decisions

1. **Computed Tower Properties**: Tower `height` and `isCapped` are computed via utility functions rather than stored properties, ensuring data consistency and immutability.

2. **String Player IDs**: boardgame.io uses string IDs (`"0"`, `"1"`) while internal arrays use numeric indices. Conversion handled at boundaries.

3. **Immer for State Updates**: All game state mutations use `produce()` from immer for guaranteed immutability.

4. **Monorepo Structure**: pnpm workspaces with shared types package enables type-safe cross-package development.

## Test Coverage

**Current Coverage**:
- Logic layer: ~85% (deck, towers, scoring)
- Game/Phases: ~0% (integration tests needed)
- Overall: ~30%

**Target**: >70% overall with integration tests

## License

ISC
