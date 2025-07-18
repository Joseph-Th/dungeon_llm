import logging
from typing import Dict, Any, TYPE_CHECKING

from game_state import GameState, GameWorld, Character
from event_executor import execute_world_mutations
from managers.quest_manager import QuestManager

if TYPE_CHECKING:
    from ai_manager import AIManager
    from display_manager import DisplayManager

class QuestHandler:

    def __init__(self, quest_manager: QuestManager):
        self.quest_manager = quest_manager

    def process_quest_intent(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        action_type = intent_data.get("action_type")
        
        # This is the fix: convert the action_type to lowercase before comparing.
        if action_type and action_type.lower() == "accept":
            return self._handle_accept_quest(game_state, world, ai_manager, intent_data)
        
        logging.warning(f"QuestHandler received an unhandled action_type: {action_type}")
        return "Failure: You're not sure how to respond to that."

    def _handle_accept_quest(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        quest_giver_name = intent_data.get("target")
        if not quest_giver_name:
            return "Failure: The AI could not determine who gave the quest."

        quest_giver = game_state.find_character_in_location(quest_giver_name, world)
        if not quest_giver:
            # Fallback to searching the whole world if the target isn't in the current location.
            char_data = world.find_character_anywhere(quest_giver_name)
            if char_data:
                quest_giver, _ = char_data
            else:
                return f"Failure: You don't see {quest_giver_name} here to accept a quest from."

        quest_offer_memory = None
        for memory in reversed(quest_giver.memory):
            if "work" in memory.lower() or "job" in memory.lower() or "task" in memory.lower() or "catch" in memory.lower():
                quest_offer_memory = memory
                break
        
        if not quest_offer_memory:
            logging.warning(f"Player tried to accept a quest from '{quest_giver.name}', but no recent offer memory was found.")
            return "Failure: They don't seem to recall offering you any work."

        quest_data = ai_manager.generate_quest_from_context(quest_giver, quest_offer_memory)

        if not quest_data:
            logging.error(f"AI failed to generate quest data from memory: '{quest_offer_memory}'")
            return "Failure: There was a misunderstanding about the details of the job."
            
        display: 'DisplayManager' = intent_data["display"]
        self.quest_manager.start_quest(game_state, quest_data, display)
        
        # Example of a hardcoded quest trigger. This can be made more robust later.
        if "grog" in quest_data.get("id", ""):
            storeroom_door = game_state.find_interactable_in_location("storeroom door", world)
            if storeroom_door and storeroom_door.state.get("locked"):
                logging.info(f"Unlocking storeroom_door as part of quest acceptance.")
                storeroom_door.state["locked"] = False
                
                current_location = game_state.get_current_location(world)
                if current_location and "salty_siren_storeroom" not in current_location.exits.values():
                    mutation = {
                        "op": "add_exit",
                        "location_id": current_location.id,
                        "exit_description": "a heavy oak door to the storeroom",
                        "destination_id": "salty_siren_storeroom"
                    }
                    execute_world_mutations(game_state, world, [mutation])

        return "Success: Quest Accepted"