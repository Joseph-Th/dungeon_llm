import logging
from typing import Dict, Any, TYPE_CHECKING

from game_state import GameState, GameWorld
from quest_manager import QuestManager

if TYPE_CHECKING:
    from ai_manager import AIManager

class QuestHandler:

    def __init__(self, quest_manager: QuestManager):
        self.quest_manager = quest_manager

    def process_quest_intent(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        action_type = intent_data.get("action_type")
        
        if action_type == "accept":
            return self._handle_accept_quest(game_state, world, ai_manager, intent_data)
        
        # Future actions like "decline" or "inquire" can be added here
        # elif action_type == "decline":
        #     return "Success: You declined the offer."
        
        logging.warning(f"QuestHandler received an unhandled action_type: {action_type}")
        return "Failure: You're not sure how to respond to that."

    def _handle_accept_quest(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        quest_giver_name = intent_data.get("target")
        if not quest_giver_name:
            return "Failure: The AI could not determine who gave the quest."

        quest_giver = game_state.find_character_in_location(quest_giver_name, world)
        if not quest_giver:
            return f"Failure: You don't see {quest_giver_name} here to accept a quest from."

        # Find the relevant memory from the quest giver that contains the offer
        quest_offer_memory = None
        for memory in reversed(quest_giver.memory):
            if "offered" in memory.lower() and "work" in memory.lower() or "quest" in memory.lower():
                quest_offer_memory = memory
                break
        
        if not quest_offer_memory:
            return "Failure: They don't seem to recall offering you any work."

        # Ask the AI to formalize the quest based on the memory
        # This assumes a new function in AIManager: generate_quest_from_context
        quest_data = ai_manager.generate_quest_from_context(quest_giver, quest_offer_memory)

        if not quest_data:
            logging.error(f"AI failed to generate quest data from memory: '{quest_offer_memory}'")
            return "Failure: There was a misunderstanding about the details of the job."
            
        self.quest_manager.start_quest(game_state, quest_data)
        
        return "Success: Quest Accepted"