import random


class ClueEngine:
    """Handles the classic 1949 cards, deck shuffling, and room connections."""
    SUSPECTS = ["Miss Scarlet", "Col. Mustard", "Mrs. White", "Mr. Green", "Mrs. Peacock", "Prof. Plum"]
    WEAPONS = ["Candlestick", "Knife", "Lead Pipe", "Revolver", "Rope", "Wrench"]
    ROOMS = ["Kitchen", "Ballroom", "Conservatory", "Billiard Room", "Library", "Study", "Hall", "Lounge",
             "Dining Room"]

    MANSION_MAP = {
        "Kitchen": ["Ballroom", "Dining Room", "Study"],
        "Ballroom": ["Kitchen", "Conservatory", "Hall"],
        "Conservatory": ["Ballroom", "Billiard Room", "Lounge"],
        "Billiard Room": ["Conservatory", "Hall", "Library", "Study"],
        "Library": ["Study", "Billiard Room"],
        "Study": ["Library", "Lounge", "Hall", "Kitchen"],
        "Hall": ["Dining Room", "Billiard Room", "Study", "Ballroom"],
        "Lounge": ["Study", "Dining Room", "Conservatory"],
        "Dining Room": ["Kitchen", "Hall", "Lounge"]
    }

    def __init__(self, num_ai=2, difficulty="Medium"):
        self.num_ai = num_ai
        self.difficulty = difficulty
        self.secret_envelope = {}
        self.player_hand = []
        self.ai_hands = []
        self.current_location = "Hall"
        self.ai_locations = ["Hall"] * num_ai

        available_suspects = list(self.SUSPECTS)
        random.shuffle(available_suspects)
        self.player_character = available_suspects.pop(0)
        self.ai_characters = [available_suspects.pop(0) for _ in range(num_ai)]
        self.setup_game()

    def setup_game(self):
        winning_s = random.choice(self.SUSPECTS)
        winning_w = random.choice(self.WEAPONS)
        winning_r = random.choice(self.ROOMS)
        self.secret_envelope = {"suspect": winning_s, "weapon": winning_w, "room": winning_r}

        full_deck = ([s for s in self.SUSPECTS if s != winning_s] +
                     [w for w in self.WEAPONS if w != winning_w] +
                     [r for r in self.ROOMS if r != winning_r])
        random.shuffle(full_deck)

        total_players = self.num_ai + 1
        cards_per_player = len(full_deck) // total_players
        self.player_hand = sorted([full_deck.pop() for _ in range(cards_per_player)])
        self.ai_hands = [[full_deck.pop() for _ in range(cards_per_player)] for _ in range(self.num_ai)]

    def get_valid_moves(self):
        """Returns adjacent rooms for the human player."""
        return self.MANSION_MAP.get(self.current_location, [])

    def get_ai_move(self, ai_index):
        """Moves an AI with strategic behavior and returns the new location string."""
        current = self.ai_locations[ai_index]
        possible = self.MANSION_MAP[current]
        
        # AI personality based on index for variety
        personality = ai_index % 3
        
        if personality == 0:
            # Explorer AI - prefers unvisited rooms
            unvisited = [room for room in possible if room not in self.ai_locations]
            if unvisited:
                new_loc = random.choice(unvisited)
            else:
                new_loc = random.choice(possible)
        elif personality == 1:
            # Strategic AI - prefers rooms with more connections
            room_scores = {}
            for room in possible:
                room_scores[room] = len(self.MANSION_MAP[room])
            new_loc = max(room_scores, key=room_scores.get)
        else:
            # Random AI with slight preference for current room's neighbors
            weights = [1.2 if room != current else 1.0 for room in possible]
            new_loc = random.choices(possible, weights=weights)[0]
        
        self.ai_locations[ai_index] = new_loc
        return new_loc
    
    def make_suggestion(self, suspect, weapon, room):
        """Process a suggestion and return if it can be disproven."""
        suggestion = {"suspect": suspect, "weapon": weapon, "room": room}
        
        # Check if any AI player can disprove
        for i, ai_hand in enumerate(self.ai_hands):
            if suspect in ai_hand:
                return {"disproven": True, "card": suspect, "player": self.ai_characters[i]}
            elif weapon in ai_hand:
                return {"disproven": True, "card": weapon, "player": self.ai_characters[i]}
            elif room in ai_hand:
                return {"disproven": True, "card": room, "player": self.ai_characters[i]}
        
        return {"disproven": False, "card": None, "player": None}
    
    def make_ai_suggestion(self, ai_index):
        """AI makes a suggestion when in a room."""
        current_room = self.ai_locations[ai_index]
        ai_hand = self.ai_hands[ai_index]
        
        # AI strategy: suggest cards they don't have
        possible_suspects = [s for s in self.SUSPECTS if s not in ai_hand]
        possible_weapons = [w for w in self.WEAPONS if w not in ai_hand]
        possible_rooms = [r for r in self.ROOMS if r not in ai_hand]
        
        # Add current room to possible rooms even if AI has it
        if current_room not in possible_rooms:
            possible_rooms.append(current_room)
        
        # Make random suggestion from available cards
        suspect = random.choice(possible_suspects) if possible_suspects else random.choice(self.SUSPECTS)
        weapon = random.choice(possible_weapons) if possible_weapons else random.choice(self.WEAPONS)
        room = current_room  # AI always suggests current room
        
        return {"suspect": suspect, "weapon": weapon, "room": room, "player": self.ai_characters[ai_index]}
    
    def check_ai_can_disprove(self, suggestion, ai_index):
        """Check if a specific AI can disprove a suggestion."""
        ai_hand = self.ai_hands[ai_index]
        if suggestion["suspect"] in ai_hand:
            return suggestion["suspect"]
        elif suggestion["weapon"] in ai_hand:
            return suggestion["weapon"]
        elif suggestion["room"] in ai_hand:
            return suggestion["room"]
        return None
    
    def make_accusation(self, suspect, weapon, room):
        """Check if the accusation is correct."""
        correct_suspect = self.secret_envelope["suspect"] == suspect
        correct_weapon = self.secret_envelope["weapon"] == weapon
        correct_room = self.secret_envelope["room"] == room
        
        return {
            "correct": correct_suspect and correct_weapon and correct_room,
            "solution": self.secret_envelope
        }
