import json
import logging
from typing import Dict
from pathlib import Path

from game_state import GameWorld, Location, Character, Item
from definitions.quests import Quest, Objective

class WorldLoader:
    def __init__(self, locations_data_dir: str):
        self.locations_path = Path(locations_data_dir)

    def load_world(self) -> GameWorld:
        logging.info(f"Loading world data from directory '{self.locations_path}'...")
        
        rebuilt_locations = {}
        try:
            if not self.locations_path.is_dir():
                raise FileNotFoundError(f"The specified location directory does not exist: {self.locations_path}")

            for location_file in self.locations_path.glob("*.json"):
                logging.info(f"  - Loading location file: {location_file.name}")
                with open(location_file, 'r') as f:
                    loc_data = json.load(f)
                
                loc_id = loc_data.get("id")
                if not loc_id:
                    logging.warning(f"    - SKIPPING: Location file {location_file.name} is missing a required 'id'.")
                    continue
                
                rebuilt_locations[loc_id] = self._rebuild_location(loc_data)
            
            if not rebuilt_locations:
                raise ValueError("No valid location files were found in the specified directory.")

            world = GameWorld(locations=rebuilt_locations)
            logging.info("World data loaded and objects built successfully.")
            return world

        except (IOError, json.JSONDecodeError, KeyError, FileNotFoundError, ValueError) as e:
            logging.critical(f"Failed to load or parse world data. Error: {e}")
            raise

    def _rebuild_character(self, char_data: Dict) -> Character:
        max_hp = char_data.get('max_hp', 20)
        hp = char_data.get('hp', max_hp)

        return Character(
            name=char_data['name'],
            description=char_data['description'],
            stats=char_data['stats'],
            inventory=char_data.get('inventory', []),
            mood=char_data.get('mood', 'neutral'),
            memory=char_data.get('memory', []),
            available_quest_ids=char_data.get('available_quest_ids', []),
            hp=hp,
            max_hp=max_hp,
            status_effects=char_data.get('status_effects', [])
        )

    def _rebuild_location(self, loc_data: Dict) -> Location:
        items = [Item(**item) for item in loc_data.get('items', [])]
        characters = [self._rebuild_character(char) for char in loc_data.get('characters', [])]

        rebuilt_quests = []
        for quest_data in loc_data.get('quests', []):
            objectives = [Objective(**obj_data) for obj_data in quest_data.get('objectives', [])]
            quest = Quest(
                id=quest_data['id'],
                name=quest_data['name'],
                description=quest_data['description'],
                required_stat=quest_data.get('required_stat'),
                required_dc=quest_data.get('required_dc', 0),
                objectives=objectives
            )
            rebuilt_quests.append(quest)
        
        return Location(
            id=loc_data['id'],
            name=loc_data['name'],
            description=loc_data['description'],
            characters=characters,
            items=items,
            exits=loc_data.get('exits', {}),
            quests=rebuilt_quests
        )