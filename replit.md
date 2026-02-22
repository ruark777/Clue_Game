# Clue Detective Game

## Overview
A web-based version of the classic 1949 Clue board game built with Python Flask. Players solve a mystery by moving through rooms, making suggestions, and accusations against AI opponents.

## Project Architecture
- **Language**: Python 3.12
- **Framework**: Flask 2.3.3
- **Entry Point**: `clue_web_dev/main.py`
- **Web App**: `clue_web_dev/web/web_app.py` - Flask routes and game session management
- **Game Engine**: `clue_web_dev/src/clue_game/engine/game_logic.py` - Core game logic (ClueEngine class)
- **Templates**: `clue_web_dev/templates/game.html` - Single-page game UI
- **Production Server**: gunicorn

## Project Structure
```
clue_web_dev/          # Main application
  main.py              # Entry point
  web/web_app.py       # Flask app with API routes
  src/clue_game/engine/game_logic.py  # Game logic engine
  templates/game.html  # Frontend template
clue_game_simple/      # Simplified version (separate)
```

## Running
- Development: `cd clue_web_dev && python main.py` (port 5000)
- Production: `gunicorn --bind=0.0.0.0:5000 --chdir=clue_web_dev web.web_app:app`

## Key Features
- Multiple AI opponents with different personalities
- Color-coded game elements (suspects, weapons, rooms)
- Detective notebook with auto-tracking
- Mansion map visualization
- Suggestion/accusation system
