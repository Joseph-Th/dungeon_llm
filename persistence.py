import json
import logging
from pathlib import Path
from typing import Optional, List, Tuple

from game_state import GameState, GameWorld, Character, Item, Location

class PersistenceManager:
    def __init__(self, save_directory: str = "saves"):
        self.save_path = Path(save_directory)
        self.save_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"PersistenceManager initialized. Save directory: '{self.save_path.resolve()}'")

    def get_save_file_path(self, slot_name: str) -> Path:
        return self.save_path / f"{slot_name}.json"

    def list_save_games(self) -> List[str]:
        return [p.stem for p in self.save_path.glob("*.json")]

    def save_game(self, game_state: GameState, world: GameWorld, slot_name: str) -> bool:
        file_path = self.get_save_file_path(slot_name)
        logging.info(f"Attempting to save game to '{file_path}'...")
        try:
            full_save_data = {
                "game_state": game_state.to_dict(),
                "game_world": world.to_dict()
            }
            with open(file_path, 'w') as f:
                json.dump(full_save_data, f, indent=4)
            logging.info(f"Game successfully saved to slot '{slot_name}'.")
            return True
        except (IOError, TypeError) as e:
            logging.error(f"Failed to save game to slot '{slot_name}'. Error: {e}")
            return False

    def load_game(self, slot_name: str) -> Optional[Tuple[GameState, GameWorld]]:
        file_path = self.get_save_file_path(slot_name)
        if not file_path.exists():
            logging.warning(f"No save file found for slot '{slot_name}'.")
            return None

        logging.info(f"Attempting to load game from '{file_path}'...")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            world_data = data['game_world']
            rebuilt_locations = {}
            for loc_id, loc_data in world_data['locations'].items():
                rebuilt_locations[loc_id] = self._rebuild_location(loc_data)
            
            world = GameWorld(locations=rebuilt_locations)

            state_data = data['game_state']
            player = self._rebuild_character(state_data['player'])
            
            game_state = GameState(
                player=player,
                current_location_id=state_data['current_location_id'],
                turn_count=state_data.get('turn_count', 0),
                minutes_elapsed=state_data.get('minutes_elapsed', 480)
            )
            
            logging.info(f"Game successfully loaded from slot '{slot_name}'.")
            return game_state, world

        except (IOError, json.JSONDecodeError, KeyError, TypeError) as e:
            logging.error(f"Failed to load game from '{file_path}'. File may be corrupt. Error: {e}")
            return None
    
    def _rebuild_character(self, char_data: dict) -> Character:
        inventory = [Item(**item) for item in char_data.get('inventory', [])]
        
        # Default HP to max_hp for backward compatibility with old saves
        max_hp = char_data.get('max_hp', 20)
        hp = char_data.get('hp', max_hp)

        return Character(
            name=char_data['name'],
            description=char_data['description'],
            stats=char_data['stats'],
            inventory=inventory,
            mood=char_data.get('mood', 'neutral'),
            memory=char_data.get('memory', []),
            hp=hp,
            max_hp=max_hp,
            status_effects=char_data.get('status_effects', [])
        )

    def _rebuild_location(self, loc_data: dict) -> Location:
        items = [Item(**item) for item in loc_data.get('items', [])]
        characters = [self._rebuild_character(char) for char in loc_data.get('characters', [])]
        return Location(
            id=loc_data['id'],
            name=loc_data['name'],
            description=loc_data['description'],
            characters=characters,
            items=items,
            exits=loc_data.get('exits', {})
        )