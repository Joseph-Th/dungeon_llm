from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
import json
import logging

from definitions.entities import Character, Item
from definitions.world_objects import Location, Interactable
from definitions.quests import Quest

@dataclass
class GameWorld:
    locations: Dict[str, Location] = field(default_factory=dict)

    def get_location(self, location_id: str) -> Optional[Location]:
        return self.locations.get(location_id)
    
    def find_character_anywhere(self, character_name: str) -> Optional[Tuple[Character, Location]]:
        for loc in self.locations.values():
            for char in loc.characters:
                if char.name.lower() == character_name.lower():
                    return char, loc
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return { "locations": {loc_id: loc.to_dict() for loc_id, loc in self.locations.items()} }

    def create_and_add_location(self, location_data: Dict[str, Any]) -> Optional[Location]:
        try:
            loc_id = location_data['id']
            
            items = [Item(**item) for item in location_data.get('items', [])]
            interactables = [Interactable(**i) for i in location_data.get('interactables', [])]
            characters = []
            for char_data in location_data.get('characters', []):
                char_init_data = {
                    'name': char_data['name'],
                    'description': char_data['description'],
                    'stats': char_data['stats'],
                    'inventory': [],
                    'mood': char_data.get('mood', 'neutral'),
                    'memory': char_data.get('memory', []),
                    'hp': char_data.get('hp', 20),
                    'max_hp': char_data.get('max_hp', 20),
                    'status_effects': char_data.get('status_effects', []),
                    'level': char_data.get('level', 1),
                    'xp': char_data.get('xp', 0),
                    'xp_to_next_level': char_data.get('xp_to_next_level', 100),
                    'armor_class': char_data.get('armor_class', 10),
                    'attack_bonus': char_data.get('attack_bonus', 0),
                    'is_hostile': char_data.get('is_hostile', False),
                    'faction': char_data.get('faction', None),
                    'schedule': char_data.get('schedule', None)
                }
                characters.append(Character(**char_init_data))

            new_location = Location(
                id=loc_id,
                name=location_data['name'],
                description=location_data['description'],
                characters=characters,
                items=items,
                interactables=interactables,
                exits=location_data.get('exits', {})
            )
            self.locations[loc_id] = new_location
            logging.info(f"Successfully created and added new location '{loc_id}' to the world.")
            return new_location
        except (KeyError, TypeError) as e:
            logging.error(f"Failed to create location from AI-generated data. Missing key or wrong type: {e}. Data: {location_data}")
            return None


@dataclass
class GameState:
    player: Character
    current_location_id: str
    turn_count: int = 0
    minutes_elapsed: int = 480 
    quest_log: Dict[str, Quest] = field(default_factory=dict)
    combat_state: Optional[Dict[str, Any]] = None
    reputation: Dict[str, int] = field(default_factory=dict)
    player_knowledge: Dict[str, Any] = field(default_factory=dict)

    @property
    def time_of_day(self) -> str:
        hour = (self.minutes_elapsed // 60) % 24
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"

    def get_current_location(self, world: GameWorld) -> Optional[Location]:
        return world.get_location(self.current_location_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player": self.player.to_dict(),
            "current_location_id": self.current_location_id,
            "turn_count": self.turn_count,
            "time_of_day": self.time_of_day,
            "minutes_elapsed": self.minutes_elapsed,
            "quest_log": {qid: q.to_dict() for qid, q in self.quest_log.items()},
            "combat_state": self.combat_state,
            "reputation": self.reputation,
            "player_knowledge": self.player_knowledge,
        }

    def get_context_string(self, world: GameWorld) -> str:
        current_location = self.get_current_location(world)
        if not current_location:
            return json.dumps({"error": f"current location '{self.current_location_id}' not found in world"})

        state_dict = self.to_dict()
        state_dict["location"] = current_location.to_dict()
        
        # Reorder player to be last for better AI context readability
        player_data = state_dict.pop("player")
        state_dict["player"] = player_data
        
        return json.dumps(state_dict, indent=2)

    def find_in_location(self, name: str, world: GameWorld) -> Optional[Tuple[Any, str]]:
        location = self.get_current_location(world)
        if not location: return None
        
        name_lower = name.lower()
        
        for char in location.characters:
            if name_lower in char.name.lower():
                return char, "character"
        for item in location.items:
            if name_lower in item.name.lower():
                return item, "item"
        for i in location.interactables:
            if name_lower in i.name.lower():
                return i, "interactable"
        return None

    def find_item_in_location(self, name: str, world: GameWorld) -> Optional[Item]:
        result = self.find_in_location(name, world)
        return result[0] if result and result[1] == "item" else None

    def find_character_in_location(self, name: str, world: GameWorld) -> Optional[Character]:
        result = self.find_in_location(name, world)
        return result[0] if result and result[1] == "character" else None
    
    def move_item_from_location_to_player(self, item: Item, world: GameWorld):
        location = self.get_current_location(world)
        if location:
            try:
                location.remove_item(item)
                self.player.add_item_to_inventory(item)
            except ValueError:
                logging.error(f"Attempted to move item '{item.name}' that was not in location '{location.id}'.")