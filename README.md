# Sweekar - AI Companion Pet

A local prototype for an AI pocket pet that evolves over time with advanced memory management.

## Features

- **Pet Naming**: Name your AI companion on first run
- **Interactive Chat**: Conversational interface with your pet (MiniMax API or template fallback)
- **Pet States**: Mood, hunger, and health tracking with visual indicators
- **Advanced Memory System**:
  - Short-term memory with score-based eviction
  - Long-term memory with retrieval tracking
  - User profile traits with strength decay
  - Emotional valence estimation
- **Data Persistence**: All data stored locally (JSON/CSV)
- **Scheduled Memory Updates**: APScheduler-based daily extraction
- **Dual Backup**: Original conversation history preserved separately

## Architecture

```
sweekar/
├── app.py                      # Streamlit UI entry point
├── chat/
│   └── chat_engine.py          # Chat processing + MiniMax API integration
├── memory/
│   ├── memory_pipeline.py      # Advanced memory pipeline
│   └── run_daily_update.py     # APScheduler-based memory updater
├── config/
│   └── pet_config.py           # Pet configuration and state management
├── storage/                    # Runtime data (gitignored)
└── backup/                     # Clean backup of conversations (gitignored)
```

## MiniMax API Configuration

Set your API key as an environment variable (never commit to git):

```bash
# Linux/Mac
export MINIMAX_API_KEY="your_api_key_here"

# Windows (CMD)
set MINIMAX_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:MINIMAX_API_KEY="your_api_key_here"
```

Or create a `.env` file (make sure `.env` is in `.gitignore`):

```
MINIMAX_API_KEY=your_api_key_here
```

**Note**: If no API key is set, the app uses template-based responses instead.

## Memory System (Advanced)

### Score-Based Eviction

Short-term memory limited to 50 entries. Eviction uses weighted scoring:

```
score = 0.5 × recency + 0.3 × importance + 0.2 × (access_count / 10)
```

- **recency**: Time-based decay over 7 days
- **importance**: Event type-based (emotion: 0.8, relationship: 0.9, goal: 0.7, preference: 0.5, fact: 0.4)
- **access_count**: Incremented on each retrieval

### Short-Term → Long-Term Promotion

Memories are promoted when:
- `score > 0.2` AND `access_count > 2`, OR
- Same event appears 2+ times within 7 days

### Trait Strength Decay

Each new evidence updates trait strength:

```
new_strength = old_strength × 0.8 + signal × 0.2
```

Trait stability levels:
- **stable**: strength > 0.7
- **developing**: strength > 0.4
- **emerging**: strength ≤ 0.4

### Long-Term Memory Decay

`retrieval_count` decrements by 1 if not retrieved for 30+ days.

## Installation

```bash
pip install streamlit apscheduler openai
```

## Running the App

```bash
cd swekar
streamlit run app.py
```

Browser will open automatically at http://localhost:8501

## Running Memory Scheduler

### As a background service (auto-updates every 24 hours):

```bash
python -m memory.run_daily_update
```

### Run once manually:

```bash
python -m memory.run_daily_update --once
```

### With custom interval:

```bash
python -m memory.run_daily_update --interval 12
```

## Data Storage

### Primary Storage (`storage/`)

| File | Description |
|------|-------------|
| `storage/conversation.jsonl` | All chat messages (append-only, gitignored) |
| `storage/short_memory.json` | Short-term memory (score-based, max 50) |
| `storage/long_memory.json` | Promoted long-term memories |
| `storage/profile_events.csv` | Raw extracted events (append-only) |
| `storage/profile_traits.csv` | User traits with strength decay |

### Configuration (`config/`)

| File | Description |
|------|-------------|
| `config/pet_config.json` | Pet name and settings (gitignored) |
| `config/pet_state.json` | Live pet state (gitignored) |

### Backup (`backup/`)

| File | Description |
|------|-------------|
| `backup/conversation_history.jsonl` | Original conversation backup (gitignored) |

**Important**: All user conversations are stored in both `storage/conversation.jsonl` (for UI) and `backup/conversation_history.jsonl` (clean backup). The backup is never modified by memory extraction and serves as a clean source for re-processing.

## Memory Pipeline Flow

1. Load recent conversations (last 7 days from JSONL)
2. Extract events, emotions, preferences (keyword matching)
3. Update short-term memory (scoring + eviction)
4. Check for promotions to long-term memory
5. Update user profile traits (strength decay)
6. Apply time-based decay
7. Persist to all storage files

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **AI**: MiniMax API (optional, template fallback available)
- **Storage**: JSONL (conversations), JSON (memories), CSV (profiles)
- **Scheduler**: APScheduler

## License

MIT
