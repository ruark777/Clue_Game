#!/usr/bin/env python3
"""
Web version of Clue Game with version management
"""

from flask import Flask, render_template, jsonify, request, session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.clue_game.engine.game_logic import ClueEngine
import json
import uuid
import random
from datetime import datetime
import os

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'clue-game-secret-key'

# Game sessions storage (in production, use database)
games = {}

class WebClueGame:
    """Web wrapper for ClueEngine with session management."""
    
    def __init__(self, game_id, num_ai=2, difficulty="Medium"):
        self.game_id = game_id
        self.game = ClueEngine(num_ai=num_ai, difficulty=difficulty)
        self.player_turn_active = True
        self.current_ai_index = 0
        self.game_log = []
        self.version = "2.0.4"
        self.created_at = datetime.now().isoformat()
        self.player_suggested_this_turn = False
        self.auto_track_notebook = True
        self.revealed_cards = set()  # Track cards that have been revealed
        
    def add_log(self, message):
        """Add message to game log with timestamp and color coding."""
        timestamp = datetime.now().strftime("%H:%M")
        # Apply color coding to the message
        colored_message = self.color_code_message(message)
        self.game_log.append(f"[{timestamp}] {colored_message}")
    
    def color_code_message(self, message):
        """Apply color coding to game elements in messages."""
        # Define unique colors for each suspect
        suspect_colors = {
            "Miss Scarlet": "#FF1493",  # Deep Pink
            "Col. Mustard": "#FFD700",  # Gold
            "Mrs. White": "#F0F8FF",    # Alice Blue
            "Mr. Green": "#32CD32",     # Lime Green
            "Mrs. Peacock": "#4169E1",  # Royal Blue
            "Prof. Plum": "#9370DB"     # Medium Purple
        }
        
        # Define colors for weapons
        weapon_colors = {
            "Candlestick": "#FFA500",   # Orange
            "Knife": "#C0C0C0",         # Silver
            "Lead Pipe": "#708090",      # Slate Gray
            "Revolver": "#8B4513",       # Saddle Brown
            "Rope": "#D2691E",          # Chocolate
            "Wrench": "#696969"         # Dim Gray
        }
        
        # Define colors for rooms
        room_colors = {
            "Kitchen": "#FF6347",        # Tomato
            "Ballroom": "#FF69B4",       # Hot Pink
            "Conservatory": "#98FB98",   # Pale Green
            "Billiard Room": "#87CEEB",  # Sky Blue
            "Library": "#DDA0DD",        # Plum
            "Study": "#F0E68C",          # Khaki
            "Hall": "#DEB887",           # Burlywood
            "Lounge": "#FFB6C1",         # Light Pink
            "Dining Room": "#20B2AA"     # Light Sea Green
        }
        
        # Apply suspect colors
        for suspect, color in suspect_colors.items():
            message = message.replace(suspect, f'<span style="color: {color}; font-weight: bold;">{suspect}</span>')
        
        # Apply weapon colors
        for weapon, color in weapon_colors.items():
            message = message.replace(weapon, f'<span style="color: {color}; font-weight: bold;">{weapon}</span>')
        
        # Apply room colors
        for room, color in room_colors.items():
            message = message.replace(room, f'<span style="color: {color}; font-weight: bold;">{room}</span>')
        
        # Apply generic player/AI indicators
        message = message.replace("(You)", '<span style="color: #00FF00; font-weight: bold;">(You)</span>')
        message = message.replace("You ", '<span style="color: #00FF00; font-weight: bold;">You</span> ')
        message = message.replace("AI", '<span style="color: #FF4500; font-weight: bold;">AI</span>')
        
        return message
    
    def track_revealed_card(self, card, revealing_player):
        """Track a card that has been revealed during gameplay."""
        if self.auto_track_notebook:
            self.revealed_cards.add(card)
            self.add_log(f"[AUTO-TRACK] {card} marked as revealed by {revealing_player}")
    
    def get_notebook_status(self):
        """Get current notebook status with all cards and their states."""
        all_cards = self.game.SUSPECTS + self.game.WEAPONS + self.game.ROOMS
        notebook_status = {}
        
        for card in all_cards:
            if card in self.game.player_hand:
                status = "in_hand"
            elif card in self.revealed_cards:
                status = "revealed"
            else:
                status = "unknown"
            
            notebook_status[card] = status
        
        return notebook_status
        
    def get_display_output(self):
        """Get formatted game output for display."""
        output = []
        output.append(f"=== CLUE GAME v{self.version} ===")
        output.append(f"Game ID: {self.game_id}")
        output.append(f"Started: {self.created_at[:10]}")
        output.append(f"File: web_app.py (Updated: 2026-02-17)")
        output.append("")
        
        # Player info
        output.append(f"Your Character: {self.game.player_character}")
        output.append(f"Current Location: {self.game.current_location}")
        output.append("")
        
        # Game log (last 10 entries)
        for log_entry in self.game_log[-10:]:
            output.append(log_entry)
        
        return "<br>".join(output)

@app.route('/')
def index():
    """Main game page."""
    return render_template('game.html')

@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Start a new game session."""
    data = request.get_json()
    game_id = str(uuid.uuid4())[:8]
    
    # Get player count and difficulty from frontend
    num_ai = data.get('num_ai', 2)  # Default to 2 AI
    difficulty = data.get('difficulty', 'Medium')  # Default to Medium
    
    game = WebClueGame(game_id, num_ai=num_ai, difficulty=difficulty)
    games[game_id] = game
    
    return jsonify({
        'game_id': game_id,
        'version': game.version,
        'output': game.get_display_output()
    })
    print(f"DEBUG: New game created with version: {game.version}")

@app.route('/api/load_game', methods=['POST'])
def load_game():
    """Load existing game by ID."""
    data = request.get_json()
    game_id = data.get('game_id')
    
    if game_id in games:
        game = games[game_id]
        return jsonify({
            'game_id': game_id,
            'version': game.version,
            'output': game.get_display_output(),
            'player_turn': game.player_turn_active
        })
    else:
        return jsonify({'error': 'Game not found'}), 404

@app.route('/api/game_info', methods=['POST'])
def get_game_info():
    """Get current game state info."""
    data = request.get_json()
    game_id = data.get('game_id')
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    
    print(f"DEBUG: game.game.current_location = '{game.game.current_location}'")
    print(f"DEBUG: type: {type(game.game.current_location)}")
    
    return jsonify({
        'current_location': game.game.current_location,
        'available_moves': game.game.get_valid_moves(),
        'player_character': game.game.player_character
    })

@app.route('/api/command', methods=['POST'])
def handle_command():
    """Process game commands."""
    data = request.get_json()
    game_id = data.get('game_id')
    command = data.get('command', '').lower().strip()
    
    # Log all incoming commands for debugging
    print(f"DEBUG: Received command: '{command}' for game {game_id}")
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    
    # Process commands
    if command == 'help':
        game.add_log("Commands: move, suggest, accuse, map, rules, notebook, players")
        response = "Help displayed"
        
    elif command == 'move' and game.player_turn_active:
        moves = game.game.get_valid_moves()
        if moves:
            game.add_log(f"Available moves: {', '.join(moves)}")
            response = "Choose room to move to"
        else:
            game.add_log("No moves available")
            response = "No moves available"
            
    elif command.startswith('move to ') and game.player_turn_active:
        room = command.replace('move to ', '').strip()
        moves = game.game.get_valid_moves()
        game.add_log(f"Trying to move to: '{room}'")
        game.add_log(f"Available moves: {moves}")
        
        # Try exact match first
        if room in moves:
            game.game.current_location = room
            game.add_log(f"You moved to {room}")
            game.player_turn_active = False
            game.player_suggested_this_turn = False
            response = f"Moved to {room}"
        else:
            # Try case-insensitive match
            room_lower = room.lower()
            moves_lower = [m.lower() for m in moves]
            if room_lower in moves_lower:
                # Find the exact room name
                exact_room = moves[moves_lower.index(room_lower)]
                game.game.current_location = exact_room
                game.add_log(f"You moved to {exact_room}")
                game.player_turn_active = False
                game.player_suggested_this_turn = False
                response = f"Moved to {exact_room}"
            else:
                game.add_log(f"Invalid move. Available: {', '.join(moves)}")
                game.add_log(f"Try typing exactly: {moves[0] if moves else 'No moves available'}")
                response = "Invalid move"
            
    elif command.startswith('suggest') and game.player_turn_active:
        # Parse suggestion command: "suggest suspect with weapon in room"
        # Handle multi-word names by looking for known game elements
        game.add_log(f"DEBUG: Raw command: '{command}'")
        parts = command.split()
        game.add_log(f"DEBUG: Parts: {parts}")
        game.add_log(f"DEBUG: Length check: {len(parts)} >= 6 = {len(parts) >= 6}")
        
        if len(parts) >= 6 and parts[0] == 'suggest':
            # Find the "with" and "in" keywords to parse properly
            with_index = -1
            in_index = -1
            
            for i, part in enumerate(parts):
                if part == 'with':
                    with_index = i
                elif part == 'in':
                    in_index = i
            
            if with_index > 1 and in_index > with_index + 1:
                # Extract suspect (everything between "suggest" and "with")
                suspect = " ".join(parts[1:with_index])
                weapon = parts[with_index + 1]
                room = " ".join(parts[in_index + 1:])
                
                # Validate extracted values
                suspects = ["Miss Scarlet", "Col. Mustard", "Mrs. White", "Mr. Green", "Mrs. Peacock", "Prof. Plum"]
                weapons = ["Candlestick", "Knife", "Lead Pipe", "Revolver", "Rope", "Wrench"]
                rooms = ["Kitchen", "Ballroom", "Conservatory", "Billiard Room", "Library", "Study", "Hall", "Lounge", "Dining Room"]
                
                # Normalize room name (handle "the Kitchen" -> "Kitchen")
                room = room.replace("the ", "").strip()
                
                if suspect in suspects and weapon in weapons and room in rooms:
                    # Check if player is in the suggested room
                    game.add_log(f"DEBUG: Current location: '{game.game.current_location}', Suggested room: '{room}'")
                    if room != game.game.current_location:
                        game.add_log(f"You must be in the {room} to make a suggestion there!")
                        game.add_log(f"You are currently in: {game.game.current_location}")
                        return jsonify({
                            'output': game.get_display_output(),
                            'response': "Must be in suggested room",
                            'player_turn': game.player_turn_active
                        })
                    
                    # Check if player already suggested this turn
                    if game.player_suggested_this_turn:
                        game.add_log("You can only make one suggestion per turn!")
                        return jsonify({
                            'output': game.get_display_output(),
                            'response': "Already suggested this turn",
                            'player_turn': game.player_turn_active
                        })
                    
                    # Make the suggestion
                    game.add_log(f"You suggest: {suspect} with {weapon} in {room}")
                    game.player_suggested_this_turn = True
                    
                    # Check if AI can disprove
                    suggestion_dict = {"suspect": suspect, "weapon": weapon, "room": room}
                    for i in range(game.game.num_ai):
                        if i != game.current_ai_index:
                            disprove = game.game.check_ai_can_disprove(suggestion_dict, i)
                            if disprove:
                                ai_char = game.game.ai_characters[i]
                                game.add_log(f"{ai_char} disproves with {disprove}")
                                game.track_revealed_card(disprove, ai_char)
                                break
                    else:
                        game.add_log("No one can disprove your suggestion")
                    
                    # Turn ends after suggestion
                    game.player_turn_active = False
                    game.player_suggested_this_turn = False
                    
                    return jsonify({
                        'output': game.get_display_output(),
                        'response': "Suggestion made",
                        'player_turn': game.player_turn_active
                    })
                else:
                    game.add_log(f"Invalid suggestion format. Could not find '{room}' in valid rooms.")
                    game.add_log(f"Valid rooms: {', '.join(rooms)}")
                    return jsonify({
                        'output': game.get_display_output(),
                        'response': "Invalid suggestion format",
                        'player_turn': game.player_turn_active
                    })
            else:
                game.add_log("Invalid suggestion format. Please use: suggest [suspect] with [weapon] in [room]")
                return jsonify({
                    'output': game.get_display_output(),
                    'response': "Invalid suggestion format",
                    'player_turn': game.player_turn_active
                })
        else:
            game.add_log("Make suggestion using the buttons above")
            return jsonify({
                'output': game.get_display_output(),
                'response': "Use suggestion interface",
                'player_turn': game.player_turn_active
            })
        
    elif command.startswith('accuse') and game.player_turn_active:
        # Parse accusation command: "accuse suspect with weapon in room"
        # Handle multi-word names by finding the "with" and "in" keywords
        parts = command.split()
        if len(parts) >= 6 and parts[0] == 'accuse':
            # Find the "with" and "in" keywords to parse properly
            with_index = -1
            in_index = -1
            
            for i, part in enumerate(parts):
                if part == 'with':
                    with_index = i
                elif part == 'in':
                    in_index = i
            
            if with_index > 1 and in_index > with_index + 1:
                # Extract suspect (everything between "accuse" and "with")
                suspect = " ".join(parts[1:with_index])
                weapon = parts[with_index + 1]
                room = " ".join(parts[in_index + 1:])
                
                # Validate extracted values
                suspects = ["Miss Scarlet", "Col. Mustard", "Mrs. White", "Mr. Green", "Mrs. Peacock", "Prof. Plum"]
                weapons = ["Candlestick", "Knife", "Lead Pipe", "Revolver", "Rope", "Wrench"]
                rooms = ["Kitchen", "Ballroom", "Conservatory", "Billiard Room", "Library", "Study", "Hall", "Lounge", "Dining Room"]
                
                # Normalize room name (handle "the Kitchen" -> "Kitchen")
                room = room.replace("the ", "").strip()
                
                if suspect in suspects and weapon in weapons and room in rooms:
                    # Make the accusation
                    game.add_log(f"You accuse: {suspect} with {weapon} in {room}")
                    
                    # Check if correct
                    if (suspect == game.game.secret_envelope['suspect'] and 
                        weapon == game.game.secret_envelope['weapon'] and 
                        room == game.game.secret_envelope['room']):
                        game.add_log(f"CORRECT! You solved the mystery!")
                        game.add_log(f"The solution was: {game.game.secret_envelope}")
                        game.player_turn_active = False  # Game over
                        return jsonify({
                            'output': game.get_display_output(),
                            'response': "Game won!",
                            'player_turn': game.player_turn_active
                        })
                    else:
                        game.add_log(f"WRONG! The solution was: {game.game.secret_envelope}")
                        game.add_log("You lose the game!")
                        game.player_turn_active = False  # Game over
                        return jsonify({
                            'output': game.get_display_output(),
                            'response': "Game lost!",
                            'player_turn': game.player_turn_active
                        })
                else:
                    game.add_log(f"Could not parse accusation. Found: suspect={suspect}, weapon={weapon}, room={room}")
                    return jsonify({
                        'output': game.get_display_output(),
                        'response': "Invalid accusation format",
                        'player_turn': game.player_turn_active
                    })
            else:
                game.add_log("Invalid accusation format. Please use: accuse [suspect] with [weapon] in [room]")
                return jsonify({
                    'output': game.get_display_output(),
                    'response': "Invalid accusation format",
                    'player_turn': game.player_turn_active
                })
        else:
            game.add_log("Make accusation using the buttons above")
            return jsonify({
                'output': game.get_display_output(),
                'response': "Use accusation interface",
                'player_turn': game.player_turn_active
            })
        
    elif command == 'map':
        response = "Map shown"
        map_str = f"""=== MANSION MAP ===<br>
    <span style='color: #FF6347; font-family: monospace; font-weight: bold;'>KITCHEN</span> ----- <span style='color: #FF69B4; font-family: monospace; font-weight: bold;'>BALLROOM</span> ----- <span style='color: #98FB98; font-family: monospace; font-weight: bold;'>CONSERVATORY</span><br>
        |           |              |<br>
    <span style='color: #20B2AA; font-family: monospace; font-weight: bold;'>DINING RM</span> --- <span style='color: #DEB887; font-family: monospace; font-weight: bold;'>HALL</span> --------- <span style='color: #87CEEB; font-family: monospace; font-weight: bold;'>BILLIARD RM</span><br>
        |           |              |<br>
    <span style='color: #FFB6C1; font-family: monospace; font-weight: bold;'>LOUNGE</span> ------ <span style='color: #F0E68C; font-family: monospace; font-weight: bold;'>STUDY</span> -------- <span style='color: #DDA0DD; font-family: monospace; font-weight: bold;'>LIBRARY</span><br>
<b>Current Locations:</b><br>
You (<span style='color: #00FF00;'>{game.game.player_character}</span>): <span style='color: #DEB887;'>{game.game.current_location}</span><br>
"""
        for i, loc in enumerate(game.game.ai_locations):
            ai_number = i + 1
            map_str += f"<span style='color: #FF4500;'>{game.game.ai_characters[i]}</span> (<span style='color: #FF4500; font-weight: bold;'>AI_" + str(ai_number) + "</span>): {loc}<br>"
        return jsonify({
            'output': map_str,
            'response': response,
            'player_turn': game.player_turn_active,
            'location': game.game.current_location
        })
        
    elif command == 'rules':
        response = "Rules shown"
        rules_str = """
=== CLUE GAME RULES ===

[bold]OBJECTIVE:[/]
Determine who committed the murder, with what weapon, and in which room.

[bold]ORDER OF OPERATIONS (Game Flow):[/]
1. YOUR TURN: Choose one action per turn
   • Move to an adjacent room (see map for connections)
   • Make a suggestion (only if in a room, one per turn)
   • Make final accusation (ends game if wrong!)

2. MOVEMENT RULES:
   • You can only move to connected rooms shown on the map
   • Each room connects to 2-3 other rooms
   • Use 'move' command to see available options

3. SUGGESTION RULES:
   • Must be in the room you're suggesting
   • Only one suggestion per turn
   • Format: "suggest [suspect] with [weapon] in [room]"
   • Only ONE card is needed to disprove (any matching card)

4. AI TURNS:
   • Press SPACE to advance through AI turns
   • AIs will move and make suggestions automatically
   • You may need to disprove AI suggestions

5. WINNING:
   • Make correct final accusation to win
   • Wrong accusation = you lose immediately!
   • Use process of elimination to deduce solution

[bold]STRATEGY TIPS:[/]
• Use 'notebook' to track your cards and revealed cards
• Auto-tracking marks cards when they're revealed (toggle with 'toggle_autotrack')
• Watch other players' suggestions carefully
• The solution cards are never in any player's hand
• Only suggest rooms you're currently in

[bold]COMMANDS:[/]
• move - See available rooms to move to
• move to [room] - Move to a specific room
• suggest [suspect] [weapon] [room] - Make suggestion
• accuse [suspect] [weapon] [room] - Make final accusation
• map - View mansion map and locations
• notebook - View your cards and revealed cards
• players - See all players and locations
• rules - Show these rules
• toggle_autotrack - Enable/disable auto-tracking
"""
        return jsonify({
            'output': rules_str,
            'response': response,
            'player_turn': game.player_turn_active
        })
        
    elif command == 'notebook':
        response = "Notebook shown"
        
        suspect_colors = {
            "Miss Scarlet": "#FF1493", "Col. Mustard": "#FFD700", "Mrs. White": "#F0F8FF",
            "Mr. Green": "#32CD32", "Mrs. Peacock": "#4169E1", "Prof. Plum": "#9370DB"
        }
        weapon_colors = {
            "Candlestick": "#FFA500", "Knife": "#C0C0C0", "Lead Pipe": "#708090",
            "Revolver": "#8B4513", "Rope": "#D2691E", "Wrench": "#696969"
        }
        room_colors = {
            "Kitchen": "#FF6347", "Ballroom": "#FF69B4", "Conservatory": "#98FB98",
            "Billiard Room": "#87CEEB", "Library": "#DDA0DD", "Study": "#F0E68C",
            "Hall": "#DEB887", "Lounge": "#FFB6C1", "Dining Room": "#20B2AA"
        }
        
        cards_str = """
<style>
.checklist-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
}
.checklist-table th {
    background: #1a1a2e;
    color: #00FF00;
    padding: 8px;
    text-align: left;
    border: 1px solid #444;
}
.checklist-table td {
    padding: 5px;
    border: 1px solid #444;
}
.checklist-checkbox {
    margin-right: 8px;
}
.card-name {
    font-weight: bold;
}
.status-in-hand {
    color: #00FF00;
}
.status-revealed {
    color: #FF6347;
    text-decoration: line-through;
}
.status-unknown {
    color: #FFFFFF;
}
</style>

<b>DETECTIVE'S CHECKLIST</b><br><br>

<b>SUSPECTS:</b><br>
<table class="checklist-table">
<tr><th>Status</th><th>Suspect</th></tr>
"""
        
        # Add suspects
        for suspect in game.game.SUSPECTS:
            if suspect in game.game.player_hand:
                status = "in_hand"
                status_text = "✓ In Hand"
                checkbox = "checked disabled"
            elif suspect in game.revealed_cards:
                status = "revealed"
                status_text = "✗ Revealed"
                checkbox = "checked disabled"
            else:
                status = "unknown"
                status_text = "? Unknown"
                checkbox = ""
            
            color = suspect_colors.get(suspect, "#FFFFFF")
            cards_str += f"""
<tr>
    <td><span class="status-{status}">{status_text}</span></td>
    <td><span class="card-name" style="color: {color};">{suspect}</span></td>
</tr>
"""
        
        cards_str += "</table><br><b>WEAPONS:</b><br><table class=\"checklist-table\"><tr><th>Status</th><th>Weapon</th></tr>"
        
        # Add weapons
        for weapon in game.game.WEAPONS:
            if weapon in game.game.player_hand:
                status = "in_hand"
                status_text = "✓ In Hand"
                checkbox = "checked disabled"
            elif weapon in game.revealed_cards:
                status = "revealed"
                status_text = "✗ Revealed"
                checkbox = "checked disabled"
            else:
                status = "unknown"
                status_text = "? Unknown"
                checkbox = ""
            
            color = weapon_colors.get(weapon, "#FFFFFF")
            cards_str += f"""
<tr>
    <td><span class="status-{status}">{status_text}</span></td>
    <td><span class="card-name" style="color: {color};">{weapon}</span></td>
</tr>
"""
        
        cards_str += "</table><br><b>ROOMS:</b><br><table class=\"checklist-table\"><tr><th>Status</th><th>Room</th></tr>"
        
        # Add rooms
        for room in game.game.ROOMS:
            if room in game.game.player_hand:
                status = "in_hand"
                status_text = "✓ In Hand"
                checkbox = "checked disabled"
            elif room in game.revealed_cards:
                status = "revealed"
                status_text = "✗ Revealed"
                checkbox = "checked disabled"
            else:
                status = "unknown"
                status_text = "? Unknown"
                checkbox = ""
            
            color = room_colors.get(room, "#FFFFFF")
            cards_str += f"""
<tr>
    <td><span class="status-{status}">{status_text}</span></td>
    <td><span class="card-name" style="color: {color};">{room}</span></td>
</tr>
"""
        
        cards_str += "</table><br>"
        cards_str += f"<b>Auto-tracking: {'ON' if game.auto_track_notebook else 'OFF'}</b><br>"
        cards_str += "Use 'toggle_autotrack' to enable/disable"
        
        return jsonify({
            'output': cards_str,
            'response': response,
            'player_turn': game.player_turn_active
        })
        
    elif command == 'toggle_autotrack':
        game.auto_track_notebook = not game.auto_track_notebook
        status = "enabled" if game.auto_track_notebook else "disabled"
        game.add_log(f"Auto-tracking {status}")
        response = f"Auto-tracking {status}"
        
    elif command == 'players':
        response = "Players shown"
        players_str = f"""
<b>Game Players:</b><br>
<br>
<span style='color: #00FF00; font-weight: bold;'>You ({game.game.player_character})</span><br>
  Character: {game.game.player_character}<br>
  Location: {game.game.current_location}<br>
  Cards: {len(game.game.player_hand)} cards<br>
<br>
"""
        suspect_colors = {
            "Miss Scarlet": "#FF1493", "Col. Mustard": "#FFD700", "Mrs. White": "#F0F8FF",
            "Mr. Green": "#32CD32", "Mrs. Peacock": "#4169E1", "Prof. Plum": "#9370DB"
        }
        
        for i, (char, loc) in enumerate(zip(game.game.ai_characters, game.game.ai_locations)):
            color = suspect_colors.get(char, "#FF4500")
            ai_number = i + 1
            players_str += f"<span style='color: {color}; font-weight: bold;'>{char}</span> (<span style='color: #FF4500; font-weight: bold;'>AI_" + str(ai_number) + "</span>)<br>"
        return jsonify({
            'output': players_str,
            'response': response,
            'player_turn': game.player_turn_active
        })
        
    elif command.startswith('disprove') and hasattr(game, 'waiting_for_disproval') and game.waiting_for_disproval:
        # Player is choosing which card to show for disproval
        card = command.replace('disprove ', '').strip()
        game.add_log(f"Received card '{card}'")
        game.add_log(f"Available cards: {game.pending_disproval_cards}")
        
        if card.lower() in [c.lower() for c in game.pending_disproval_cards]:
            # Player chose a valid card
            game.add_log(f"You disprove with {card}")
            game.add_log(f"{game.pending_suggestion['player']}'s suggestion was disproven")
            
            # Clear pending state
            game.waiting_for_disproval = False
            game.pending_suggestion = None
            game.pending_disproval_cards = None
            
            # Continue with AI turn
            game.current_ai_index += 1
            if game.current_ai_index >= game.game.num_ai:
                game.current_ai_index = 0
                game.player_turn_active = True
                game.add_log("Your turn!")
            
            response = "Disproval completed"
        else:
            game.add_log(f"Invalid card choice. Available: {', '.join(game.pending_disproval_cards)}")
            response = "Invalid card choice"
        
    elif command == 'space' and not game.player_turn_active and not (hasattr(game, 'waiting_for_disproval') and game.waiting_for_disproval):
        # AI turn
        ai_char = game.game.ai_characters[game.current_ai_index]
        ai_number = game.current_ai_index + 1
        new_loc = game.game.get_ai_move(game.current_ai_index)
        game.add_log(f"{ai_char} (AI_" + str(ai_number) + ") moved to {new_loc}")
        
        # AI suggestion
        if random.random() < 0.5:
            suggestion = game.game.make_ai_suggestion(game.current_ai_index)
            game.add_log(f"{suggestion['player']} suggests: {suggestion['suspect']} with {suggestion['weapon']} in {suggestion['room']}")
            
            # Check if other players can disprove (starting with player, then other AIs)
            disproven = False
            disproving_player = None
            disproving_card = None
            
            game.add_log("Checking for disproval...")
            
            # Check human player first
            player_cards = []
            if suggestion['suspect'] in game.game.player_hand:
                player_cards.append(suggestion['suspect'])
            if suggestion['weapon'] in game.game.player_hand:
                player_cards.append(suggestion['weapon'])
            if suggestion['room'] in game.game.player_hand:
                player_cards.append(suggestion['room'])
            
            if player_cards:
                # Player can disprove - wait for player choice
                game.add_log(f"You can disprove with: {', '.join(player_cards)}")
                game.add_log("Choose which card to show...")
                # Store suggestion info for later disproval
                game.pending_suggestion = suggestion
                game.pending_disproval_cards = player_cards
                game.waiting_for_disproval = True
                return jsonify({
                    'output': game.get_display_output(),
                    'response': "Waiting for disproval choice",
                    'player_turn': False,  # Still AI's turn, but waiting for player
                    'waiting_for_disproval': True,
                    'suggestion': suggestion,
                    'available_cards': player_cards
                })
            else:
                game.add_log("You cannot disprove - checking other AIs...")
                # Check other AIs (in order starting from next AI)
                for i in range(1, game.game.num_ai + 1):
                    ai_to_check = (game.current_ai_index + i) % game.game.num_ai
                    if ai_to_check != game.current_ai_index:
                        ai_to_check_number = ai_to_check + 1
                        disproving_card = game.game.check_ai_can_disprove(suggestion, ai_to_check)
                        if disproving_card:
                            disproving_player = game.game.ai_characters[ai_to_check]
                            disproven = True
                            game.add_log(f"{disproving_player} (AI_" + str(ai_to_check_number) + ") disproves with {disproving_card}")
                            game.track_revealed_card(disproving_card, disproving_player)
                            break
                        else:
                            game.add_log(f"{game.game.ai_characters[ai_to_check]} (AI_" + str(ai_to_check_number) + ") cannot disprove")
            
            if not disproven:
                game.add_log("No one can disprove the suggestion")
        
        # AI accusation (rare, makes game more interesting)
        if random.random() < 0.1:  # 10% chance to make accusation
            ai_char = game.game.ai_characters[game.current_ai_index]
            ai_number = game.current_ai_index + 1
            # AI makes random accusation (simple strategy)
            ai_hand = game.game.ai_hands[game.current_ai_index]
            possible_suspects = [s for s in game.game.SUSPECTS if s not in ai_hand]
            possible_weapons = [w for w in game.game.WEAPONS if w not in ai_hand]
            possible_rooms = [r for r in game.game.ROOMS if r not in ai_hand]
            
            accusation = {
                'suspect': random.choice(possible_suspects) if possible_suspects else random.choice(game.game.SUSPECTS),
                'weapon': random.choice(possible_weapons) if possible_weapons else random.choice(game.game.WEAPONS),
                'room': random.choice(possible_rooms) if possible_rooms else random.choice(game.game.ROOMS),
                'player': ai_char
            }
            
            game.add_log(f"{ai_char} (AI_" + str(ai_number) + ") makes final accusation: {accusation['suspect']} with {accusation['weapon']} in {accusation['room']}")
            
            # Check if correct
            if (accusation['suspect'] == game.game.secret_envelope['suspect'] and 
                accusation['weapon'] == game.game.secret_envelope['weapon'] and 
                accusation['room'] == game.game.secret_envelope['room']):
                game.add_log(f"CORRECT! {ai_char} (AI_" + str(ai_number) + ") solved the mystery!")
                game.add_log(f"The solution was: {game.game.secret_envelope}")
                game.add_log("You lose - AI won the game!")
                game.player_turn_active = False  # Game over
            else:
                game.add_log(f"WRONG! {ai_char} (AI_" + str(ai_number) + ")'s accusation was incorrect")
                game.add_log(f"{ai_char} (AI_" + str(ai_number) + ") is out of the game!")
                # Remove this AI from future turns
                game.game.ai_characters[game.current_ai_index] = None
        
        game.current_ai_index += 1
        if game.current_ai_index >= game.game.num_ai:
            game.current_ai_index = 0
            game.player_turn_active = True
            game.player_suggested_this_turn = False
            game.add_log("Your turn!")
        
        response = "AI turn completed"
        
    else:
        # Better error handling for unknown commands
        if command.strip():
            game.add_log(f"Unknown command: '{command}'")
            game.add_log("Type 'help' for available commands")
        else:
            game.add_log("Empty command - type 'help' for available commands")
        response = "Unknown command"
    
    return jsonify({
        'output': game.get_display_output(),
        'response': response,
        'player_turn': game.player_turn_active,
        'location': game.game.current_location
    })

@app.route('/api/save_game', methods=['POST'])
def save_game():
    """Save game state."""
    data = request.get_json()
    game_id = data.get('game_id')
    
    if game_id in games:
        game = games[game_id]
        # In production, save to database
        return jsonify({
            'saved': True,
            'game_id': game_id,
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify({'error': 'Game not found'}), 404

@app.route('/api/list_games', methods=['GET'])
def list_games():
    """List all active games with versions."""
    game_list = []
    for game_id, game in games.items():
        game_list.append({
            'game_id': game_id,
            'version': game.version,
            'created': game.created_at,
            'current_location': game.game.current_location,
            'player_character': game.game.player_character
        })
    
    return jsonify({'games': game_list})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
