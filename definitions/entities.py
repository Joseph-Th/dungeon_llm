from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Item:
    name: str
    description: str
    category: str = "misc"
    value: int = 0
    
    equipment_slot: Optional[str] = None
    stat_bonuses: Dict[str, int] = field(default_factory=dict)

    use_effect: Dict[str, Any] = field(default_factory=dict)
    damage_dice: Optional[str] = None
    damage_type: Optional[str] = None
    unlocks_id: Optional[str] = None
    owner: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "value": self.value,
            "equipment_slot": self.equipment_slot,
            "stat_bonuses": self.stat_bonuses,
            "use_effect": self.use_effect,
            "damage_dice": self.damage_dice,
            "damage_type": self.damage_type,
            "unlocks_id": self.unlocks_id,
            "owner": self.owner,
        }

@dataclass
class Character:
    name: str
    description: str
    stats: Dict[str, int]
    inventory: List[Item] = field(default_factory=list)
    equipment: Dict[str, Optional[Item]] = field(default_factory=dict)
    
    mood: str = "neutral"
    memory: List[str] = field(default_factory=list)
    personality_tags: List[str] = field(default_factory=list)
    available_quest_ids: List[str] = field(default_factory=list)
    hp: int = 20
    max_hp: int = 20
    status_effects: List[str] = field(default_factory=list)
    
    level: int = 1
    xp: int = 0
    xp_to_next_level: int = 100
    money: int = 10
    
    base_armor_class: int = 10
    base_attack_bonus: int = 0
    is_hostile: bool = False

    faction: Optional[str] = None
    schedule: Optional[Dict[str, str]] = None
    is_hidden: bool = False

    def get_total_armor_class(self) -> int:
        ac_bonus = 0
        for item in self.equipment.values():
            if item:
                ac_bonus += item.stat_bonuses.get("armor_class", 0)
        return self.base_armor_class + ac_bonus

    def get_total_attack_bonus(self) -> int:
        bonus = 0
        main_hand = self.equipment.get("main_hand")
        if main_hand:
            bonus += main_hand.stat_bonuses.get("attack_bonus", 0)
        return self.base_attack_bonus + bonus

    def get_damage_dice(self) -> str:
        main_hand = self.equipment.get("main_hand")
        if main_hand and main_hand.damage_dice:
            return main_hand.damage_dice
        return "1d4" 

    def add_item_to_inventory(self, item: Item):
        self.inventory.append(item)

    def remove_item_from_inventory(self, item: Item):
        self.inventory.remove(item)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "stats": self.stats,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipment": {slot: item.to_dict() for slot, item in self.equipment.items() if item},
            "mood": self.mood,
            "memory": self.memory,
            "personality_tags": self.personality_tags,
            "available_quest_ids": self.available_quest_ids,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "status_effects": self.status_effects,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "money": self.money,
            "base_armor_class": self.base_armor_class,
            "base_attack_bonus": self.base_attack_bonus,
            "is_hostile": self.is_hostile,
            "faction": self.faction,
            "schedule": self.schedule,
            "is_hidden": self.is_hidden,
        }