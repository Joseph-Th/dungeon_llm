import logging
from typing import Dict, Any, TYPE_CHECKING

from game_state import GameState, GameWorld

if TYPE_CHECKING:
    from ai_manager import AIManager

class ActionProcessor:

    def process_action(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        intent = intent_data.get("intent")
        
        if intent == "take_item":
            return self._handle_take_item(game_state, world, intent_data)
        elif intent == "move":
            return self._handle_move(game_state, world, ai_manager, intent_data)
        elif intent == "pass_time":
            return self._handle_pass_time(game_state, world, intent_data)
        
        logging.warning(f"No state-changing action found for intent '{intent}'.")
        return "Automatic Success"

    def _handle_take_item(self, game_state: GameState, world: GameWorld, intent_data: Dict[str, Any]) -> str:
        target_name = intent_data.get("target")
        if not target_name:
            logging.warning("AI intent 'take_item' was missing a 'target'.")
            return "Failure: The AI could not determine what item you wanted to take."

        item_to_take = game_state.find_item_in_location(target_name, world)

        if item_to_take:
            game_state.move_item_from_location_to_player(item_to_take, world)
            logging.info(f"Player took '{item_to_take.name}'. State updated.")
            return "Success"
        else:
            logging.info(f"Player tried to take '{target_name}', but it was not found in the location.")
            return f"Failure: The '{target_name}' is not here."

    def _handle_move(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        target_id = intent_data.get("target")
        if not target_id:
            logging.warning("AI intent 'move' was missing a 'target' location ID.")
            return "Failure: The AI could not determine where you wanted to go."
        
        current_location = game_state.get_current_location(world)
        if not current_location:
            logging.error(f"Player is in a non-existent location: {game_state.current_location_id}")
            return "Failure: You are lost in the void."

        exit_description = ""
        is_valid_exit = False
        for desc, dest_id in current_location.exits.items():
            if dest_id == target_id:
                is_valid_exit = True
                exit_description = desc
                break

        if is_valid_exit:
            destination = world.get_location(target_id)
            if destination:
                game_state.current_location_id = target_id
                logging.info(f"Player moved from '{current_location.id}' to '{target_id}'. State updated.")
                return "Success"
            else:
                logging.warning(f"Exit '{exit_description}' points to a non-existent location '{target_id}'. Attempting dynamic generation.")
                
                location_data = ai_manager.generate_new_location(
                    source_location=current_location,
                    exit_description=exit_description,
                    new_location_id=target_id
                )
                
                if location_data:
                    newly_created_location = world.create_and_add_location(location_data)
                    if newly_created_location:
                        game_state.current_location_id = target_id
                        logging.info(f"Dynamically created and moved player to '{target_id}'.")
                        return "Success"
                    else:
                        logging.error(f"AI generated data for '{target_id}', but it was invalid and could not be added to the world.")
                        return "Failure: The way is blocked by a shimmer of unreality."
                else:
                    logging.error(f"AI failed to generate data for new location '{target_id}'.")
                    return "Failure: The way is blocked by mysterious forces."
        else:
            logging.info(f"Player tried to move to invalid destination '{target_id}' from '{current_location.id}'.")
            return "Failure: You can't seem to find a way to do that."
    
    def _handle_pass_time(self, game_state: GameState, world: GameWorld, intent_data: Dict[str, Any]) -> str:
        duration = intent_data.get("duration")
        if not isinstance(duration, int) or duration <= 0:
            logging.warning(f"AI intent 'pass_time' had invalid duration: {duration}.")
            return "Failure: The AI could not determine how long you wanted to wait."
        
        game_state.minutes_elapsed += duration
        logging.info(f"Player passed time by {duration} minutes. New time: {game_state.minutes_elapsed}")
        return "Success"