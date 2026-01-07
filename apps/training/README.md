# VerticalVictory Training Environment

Python Gymnasium environment for training PPO agents to play the "5 Towers" card game.

## Setup

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Development

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=five_towers --cov-report=html

# Format code
poetry run black five_towers tests scripts

# Lint code
poetry run ruff check five_towers tests scripts
```

## Training

```bash
# Train PPO agent
poetry run python scripts/train_ppo.py

# Evaluate agent
poetry run python scripts/evaluate_agent.py

# Export to ONNX
poetry run python scripts/export_onnx.py
```

## Project Structure

```
five_towers/
├── env.py              # Gymnasium environment
├── game_logic/
│   ├── state.py        # Game state dataclass
│   ├── deck.py         # Deck generation
│   ├── rules.py        # Move validation
│   ├── scoring.py      # Score calculation
│   └── phases/
│       ├── bidding.py  # Bidding phase logic
│       └── building.py # Building phase logic
├── agents/
│   ├── random_agent.py
│   └── rule_agent.py
└── utils/
    ├── rewards.py      # Reward calculation
    └── masks.py        # Action masking
```
