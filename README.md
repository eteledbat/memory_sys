# Sweekar - AI Companion Pet

A local prototype for an AI pocket pet that evolves over time with memory.

## Features

- **Pet Naming**: Name your AI companion on first run
- **Chat Interface**: Interactive conversation with your pet
- **Pet States**: Mood, hunger, and health tracking
- **Memory System**: Short-term and long-term memory with automatic extraction
- **Data Persistence**: All data stored locally in JSON/CSV files

## Project Structure

```
sweekar/
├── app.py                      # Main Streamlit UI entry
├── chat/
│   └── chat_engine.py          # Chat processing and response generation
├── memory/
│   ├── memory_pipeline.py      # Memory extraction from conversations
│   └── run_daily_update.py     # Scheduled memory update scheduler
├── config/
│   └── pet_config.py           # Pet configuration and state management
├── storage/                    # Data storage (created on first run)
│   ├── conversation.jsonl      # Chat history
│   ├── short_memory.csv        # Short-term memory
│   ├── long_memory.csv         # Long-term memory
│   ├── user_profile.csv        # User traits and preferences
│   └── pet_state.csv           # Pet state snapshot
└── config/
    ├── pet_config.json         # Pet name and settings
    └── pet_state.json          # Live pet state
```

## Installation

```bash
pip install streamlit apscheduler
```

## Running the App

```bash
cd sweekar
streamlit run app.py
```

## Running Memory Scheduler

### As a background scheduler (24-hour interval):
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

## Data Storage Locations

| File | Description |
|------|-------------|
| `storage/conversation.jsonl` | All chat messages (append-only) |
| `storage/short_memory.csv` | Recent memories (last 100 entries) |
| `storage/long_memory.csv` | Important/promoted memories |
| `storage/user_profile.csv` | User traits extracted from chat |
| `config/pet_config.json` | Pet name and settings |
| `config/pet_state.json` | Current pet state (mood, hunger, health) |

## Memory Pipeline

The memory system automatically:
1. Loads recent conversations (last 7 days)
2. Extracts events, emotions, and preferences
3. Updates short-term memory (recent events)
4. Promotes frequent events to long-term memory
5. Updates user profile traits with confidence scores
6. Snapshots pet state to CSV

## Notes

- JSONL file uses append-only mode with fsync for safety
- Memory entries have importance, recency, and access tracking
- User traits use strength scoring (0.0-1.0) that evolves over time
- Scheduler runs as a separate process from the main UI
