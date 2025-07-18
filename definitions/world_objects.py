from dataclasses import dataclass, field
from typing import List, Dict, Any

from definitions.entities import Character, Item
from definitions.quests import Quest

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
    quests: List[Quest] = field(default_factory=list)

    def remove_item(self, item: Item):
        self.items.remove(item)

    def add_character(self, character: Character):
        self.characters.append(character)

    def remove_character(self, character: Character):
        self.characters.remove(character)
        
    def get_quest_by_id(self, quest_id: str) -> Quest | None:
        """Finds a quest in this location by its ID."""
        for quest in self.quests:
            if quest.id == quest_id:
                return quest
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "characters": [char.to_dict() for char in self.characters],
            "items": [item.to_dict() for item in self.items],
            "interactables": [i.to_dict() for i in self.interactables],
            "exits": self.exits,
            "quests": [q.to_dict() for q in self.quests]
        }