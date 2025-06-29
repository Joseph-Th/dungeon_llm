import logging
from typing import Dict, Any, TYPE_CHECKING

from definitions.entities import Character, Item
from game_state import GameState, GameWorld

if TYPE_CHECKING:
    from ai_manager import AIManager

class ItemHandler:

    def process_item_intent(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        intent = intent_data.get("intent")
        
        if intent == "use_item":
            return self._handle_use_item(game_state, world, intent_data)
        elif intent == "drop_item":
            return self._handle_drop_item(game_state, world, intent_data)
        elif intent == "give_item":
            return self._handle_give_item(game_state, world, intent_data)
        
        logging.warning(f"ItemHandler received an unhandled intent: {intent}")
        return "Failure: The world doesn't know how to do that."

    def _find_item_in_inventory(self, player: Character, item_name: str) -> Item | None:
        if not player.inventory: return None
        for item in player.inventory:
            if item_name.lower() in item.name.lower():
                return item
        return None

    def _handle_use_item(self, game_state: GameState, world: GameWorld, intent_data: Dict[str, Any]) -> str:
        item_name = intent_data.get("target")
        if not item_name:
            return "Failure: You need to specify what item to use."

        item_to_use = self._find_item_in_inventory(game_state.player, item_name)
        if not item_to_use:
            return f"Failure: You do not have a '{item_name}'."
        
        if not item_to_use.use_effect:
            return f"Failure: The {item_to_use.name} doesn't seem to have a use."

        effect_op = item_to_use.use_effect.get("op")
        if effect_op == "heal":
            amount = item_to_use.use_effect.get("amount", 0)
            game_state.player.hp = min(game_state.player.max_hp, game_state.player.hp + amount)
            logging.info(f"Player used {item_to_use.name}, healing for {amount}. New HP: {game_state.player.hp}")
            if item_to_use.category == "potion":
                game_state.player.remove_item_from_inventory(item_to_use)
            return "Success"

        elif effect_op == "unlock":
            target_on_name = intent_data.get("target_on")
            if not target_on_name:
                return "Failure: What do you want to use the key on?"
            
            found_in_location = game_state.find_in_location(target_on_name, world)
            if not found_in_location:
                 return f"Failure: You don't see a '{target_on_name}' to use this on."
            
            target_obj, obj_type = found_in_location
            if obj_type != "interactable":
                return f"Failure: You can't use the key on a {obj_type}."

            if item_to_use.unlocks_id == target_obj.id and target_obj.state.get("locked"):
                target_obj.state["locked"] = False
                logging.info(f"Player used {item_to_use.name} to unlock {target_obj.name}.")
                return "Success"
            else:
                return f"Failure: It doesn't seem to work on the {target_obj.name}."

        return f"Failure: You can't figure out how to use the {item_to_use.name}."

    def _handle_drop_item(self, game_state: GameState, world: GameWorld, intent_data: Dict[str, Any]) -> str:
        item_name = intent_data.get("target")
        if not item_name:
            return "Failure: You need to specify what to drop."

        item_to_drop = self._find_item_in_inventory(game_state.player, item_name)
        if not item_to_drop:
            return f"Failure: You do not have a '{item_name}'."

        location = game_state.get_current_location(world)
        if not location:
            return "Failure: You are in a void and cannot drop things here."
        
        game_state.player.remove_item_from_inventory(item_to_drop)
        location.items.append(item_to_drop)
        logging.info(f"Player dropped '{item_to_drop.name}' in '{location.id}'.")
        return "Success"

    def _handle_give_item(self, game_state: GameState, world: GameWorld, intent_data: Dict[str, Any]) -> str:
        item_name = intent_data.get("target")
        recipient_name = intent_data.get("recipient")

        if not item_name or not recipient_name:
            return "Failure: You need to specify both an item and who to give it to."
        
        item_to_give = self._find_item_in_inventory(game_state.player, item_name)
        if not item_to_give:
            return f"Failure: You do not have a '{item_name}'."
        
        recipient = game_state.find_character_in_location(recipient_name, world)
        if not recipient:
            return f"Failure: You don't see '{recipient_name}' here."

        game_state.player.remove_item_from_inventory(item_to_give)
        recipient.add_item_to_inventory(item_to_give)
        logging.info(f"Player gave '{item_to_give.name}' to NPC '{recipient.name}'.")
        return "Success"