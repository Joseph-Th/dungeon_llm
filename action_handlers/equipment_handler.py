import logging
from typing import Dict, Any, TYPE_CHECKING

from definitions.entities import Character, Item
from game_state import GameState, GameWorld

if TYPE_CHECKING:
    from ai_manager import AIManager

class EquipmentHandler:

    def process_equipment_intent(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        intent = intent_data.get("intent")
        
        if intent == "equip":
            return self._handle_equip(game_state, intent_data)
        elif intent == "unequip":
            return self._handle_unequip(game_state, intent_data)
        
        logging.warning(f"EquipmentHandler received an unhandled intent: {intent}")
        return "Failure: The world doesn't know how to do that."

    def _find_item_in_inventory(self, player: Character, item_name: str) -> Item | None:
        if not player.inventory: return None
        for item in player.inventory:
            if item_name.lower() in item.name.lower():
                return item
        return None

    def _handle_equip(self, game_state: GameState, intent_data: Dict[str, Any]) -> str:
        item_name = intent_data.get("target")
        if not item_name:
            return "Failure: You need to specify what item to equip."

        item_to_equip = self._find_item_in_inventory(game_state.player, item_name)
        if not item_to_equip:
            return f"Failure: You do not have a '{item_name}' in your inventory."
        
        slot = item_to_equip.equipment_slot
        if not slot:
            return f"Failure: The {item_to_equip.name} is not something you can equip."

        # Unequip any item currently in that slot
        currently_equipped_item = game_state.player.equipment.get(slot)
        if currently_equipped_item:
            game_state.player.equipment[slot] = None
            game_state.player.add_item_to_inventory(currently_equipped_item)
            logging.info(f"Player automatically unequipped '{currently_equipped_item.name}' to make room for '{item_to_equip.name}'.")

        # Equip the new item
        game_state.player.equipment[slot] = item_to_equip
        game_state.player.remove_item_from_inventory(item_to_equip)
        logging.info(f"Player equipped '{item_to_equip.name}' into slot '{slot}'.")

        return f"Success: Equipped {item_to_equip.name}"

    def _handle_unequip(self, game_state: GameState, intent_data: Dict[str, Any]) -> str:
        item_name = intent_data.get("target")
        if not item_name:
            return "Failure: You need to specify what item to unequip."

        item_to_unequip = None
        target_slot = None

        # Find the item in the equipment slots
        for slot, item in game_state.player.equipment.items():
            if item and item_name.lower() in item.name.lower():
                item_to_unequip = item
                target_slot = slot
                break

        if not item_to_unequip or not target_slot:
            return f"Failure: You do not have a '{item_name}' equipped."
        
        # Move item from equipment to inventory
        game_state.player.equipment[target_slot] = None
        game_state.player.add_item_to_inventory(item_to_unequip)
        logging.info(f"Player unequipped '{item_to_unequip.name}' from slot '{target_slot}'.")

        return f"Success: Unequipped {item_to_unequip.name}"