from dataclasses import dataclass, field
from typing import List, Dict, Any

from definitions.entities import Character, Item

@dataclass
class Interactable:
    id: str
    name: str
    description: str
    state: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "state": self.state
        }

@dataclass
class Location:
    id: str
    name: str
    description: str
    characters: List[Character] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    interactables: List[Interactable] = field(default_factory=list)
    exits: Dict[str, str] = field(default_factory=dict)

    def remove_item(self, item: Item):
        self.items.remove(item)

    def add_character(self, character: Character):
        self.characters.append(character)

    def remove_character(self, character: Character):
        self.characters.remove(character)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "characters": [char.to_dict() for char in self.characters],
            "items": [item.to_dict() for item in self.items],
            "interactables": [i.to_dict() for i in self.interactables],
            "exits": self.exits,
        }