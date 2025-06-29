import logging
from typing import Dict, Any, TYPE_CHECKING

from definitions.entities import Item
from game_state import GameState, GameWorld

if TYPE_CHECKING:
    from ai_manager import AIManager

class InteractionHandler:

    def process_interaction_intent(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        intent = intent_data.get("intent")
        
        if intent == "interact":
            return self._handle_interact(game_state, world, intent_data)
        elif intent == "look":
            return self._handle_look(game_state, world, intent_data)
        
        logging.warning(f"InteractionHandler received an unhandled intent: {intent}")
        return "Failure: The world doesn't know how to do that."
    
    def _handle_look(self, game_state: GameState, world: GameWorld, intent_data: Dict[str, Any]) -> str:
        target_name = intent_data.get("target")

        if not target_name:
            logging.info("Player looked at surroundings (no specific target).")
            return "Automatic Success: Look at surroundings"

        target_obj, obj_type = None, None
        
        found_in_location = game_state.find_in_location(target_name, world)
        if found_in_location:
            target_obj, obj_type = found_in_location
        
        if not target_obj and game_state.player.inventory:
            player_item = next((item for item in game_state.player.inventory if target_name.lower() in item.name.lower()), None)
            if player_item:
                target_obj = player_item
                obj_type = "item_in_inventory"
        
        if not target_obj:
            return f"Failure: You don't see any '{target_name}' here."

        return f"Success: Look at {obj_type} - {target_obj.name}"

    def _handle_interact(self, game_state: GameState, world: GameWorld, intent_data: Dict[str, Any]) -> str:
        target_name = intent_data.get("target")
        if not target_name:
            return "Failure: You need to specify what to interact with."

        found_in_location = game_state.find_in_location(target_name, world)
        if not found_in_location:
            return f"Failure: You can't seem to find a '{target_name}' here."

        target_obj, obj_type = found_in_location
        if obj_type != "interactable":
            return f"Failure: You can't seem to interact with the '{target_name}' in that way."

        if target_obj.state.get("locked"):
            return f"Failure: The {target_obj.name} is locked."

        if 'container' in target_obj.state:
            if not target_obj.state.get('opened'):
                target_obj.state['opened'] = True
                logging.info(f"Player opened container '{target_obj.name}'.")
                
                location = game_state.get_current_location(world)
                if not location: return "Failure: Cannot interact without a valid location."

                loot = target_obj.state.get('container', [])
                if loot:
                    for item_data in loot:
                        location.items.append(Item(**item_data))
                    target_obj.state['container'] = []
                    return "Success: Open and loot"
                else:
                    return "Success: Open empty"
            else:
                return "Failure: It is already open."
        
        if 'toggled' in target_obj.state:
            current_state = target_obj.state['toggled']
            target_obj.state['toggled'] = not current_state
            logging.info(f"Player toggled '{target_obj.name}' from {current_state} to {not current_state}.")
            return "Success"
            
        return f"Failure: You're not sure how to interact with the {target_obj.name}."