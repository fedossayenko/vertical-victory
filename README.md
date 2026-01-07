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
│   ├── game-core/          # JS game logic (boardgame.io) - TODO
│   └── shared-types/       # Shared TypeScript types - TODO
├── apps/
│   ├── web-app/            # React + Vite frontend - TODO
│   └── training/           # Python Gymnasium + SB3 ✅
├── models/                 # Trained ONNX models
└── README.md
```

## Quick Start

### Python Training Environment

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

### Development Status

- [x] Python game logic implementation
- [x] Gymnasium environment
- [x] Unit tests
- [ ] Training scripts
- [ ] ONNX export
- [ ] JavaScript game logic
- [ ] React UI
- [ ] Browser AI inference

## License

ISC
