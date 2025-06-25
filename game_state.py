from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class Item:
    name: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description}

@dataclass
class Character:
    name: str
    description: str
    stats: Dict[str, int]
    inventory: List[Item] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "stats": self.stats,
            "inventory": [item.to_dict() for item in self.inventory],
        }

@dataclass
class Location:
    name: str
    description: str
    characters: List[Character] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "characters": [char.to_dict() for char in self.characters],
            "items": [item.to_dict() for item in self.items],
        }

@dataclass
class GameState:
    player: Character
    current_location: Location
    turn_count: int = 0

    def get_context_string(self) -> str:
        state_dict = {
            "player": self.player.to_dict(),
            "location": self.current_location.to_dict(),
            "turn_count": self.turn_count,
        }
        return json.dumps(state_dict, indent=2)
    
    def find_character_in_location(self, name: str) -> Optional[Character]:
        for char in self.current_location.characters:
            if char.name.lower() == name.lower():
                return char
        return None

    def find_item_in_location(self, name: str) -> Optional[Item]:
        for item in self.current_location.items:
            if item.name.lower() == name.lower():
                return item
        return None