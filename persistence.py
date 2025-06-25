import json
import logging
from pathlib import Path
from typing import Optional, List

from game_state import GameState, Character, Item, Location

class PersistenceManager:
    def __init__(self, save_directory: str = "saves"):
        self.save_path = Path(save_directory)
        self.save_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"PersistenceManager initialized. Save directory: '{self.save_path.resolve()}'")

    def get_save_file_path(self, slot_name: str) -> Path:
        return self.save_path / f"{slot_name}.json"

    def list_save_games(self) -> List[str]:
        return [p.stem for p in self.save_path.glob("*.json")]

    def save_game(self, game_state: GameState, slot_name: str) -> bool:
        file_path = self.get_save_file_path(slot_name)
        logging.info(f"Attempting to save game to '{file_path}'...")
        try:
            state_dict = game_state.to_dict()
            with open(file_path, 'w') as f:
                json.dump(state_dict, f, indent=4)
            logging.info(f"Game successfully saved to slot '{slot_name}'.")
            return True
        except (IOError, TypeError) as e:
            logging.error(f"Failed to save game to slot '{slot_name}'. Error: {e}")
            return False

    def load_game(self, slot_name: str) -> Optional[GameState]:
        file_path = self.get_save_file_path(slot_name)
        if not file_path.exists():
            logging.warning(f"No save file found for slot '{slot_name}'.")
            return None

        logging.info(f"Attempting to load game from '{file_path}'...")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            player_data = data['player']
            player_inventory = [Item(**item) for item in player_data.get('inventory', [])]
            player = Character(
                name=player_data['name'],
                description=player_data['description'],
                stats=player_data['stats'],
                inventory=player_inventory
            )

            location_data = data['location']
            location_items = [Item(**item) for item in location_data.get('items', [])]
            location_characters = []
            for char_data in location_data.get('characters', []):
                char_inventory = [Item(**item) for item in char_data.get('inventory', [])]
                location_characters.append(Character(
                    name=char_data['name'],
                    description=char_data['description'],
                    stats=char_data['stats'],
                    inventory=char_inventory
                ))
            
            location = Location(
                name=location_data['name'],
                description=location_data['description'],
                characters=location_characters,
                items=location_items
            )
            
            game_state = GameState(
                player=player,
                current_location=location,
                turn_count=data.get('turn_count', 0)
            )
            
            logging.info(f"Game successfully loaded from slot '{slot_name}'.")
            return game_state

        except (IOError, json.JSONDecodeError, KeyError, TypeError) as e:
            logging.error(f"Failed to load game from '{file_path}'. File may be corrupt. Error: {e}")
            return None