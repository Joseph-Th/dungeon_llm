import logging
from typing import Dict, Any, TYPE_CHECKING

from game_state import GameState, GameWorld

if TYPE_CHECKING:
    from ai_manager import AIManager

class DialogueHandler:

    def process_dialogue_intent(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        target_name = intent_data.get("target")
        if not target_name:
            logging.warning("Dialogue intent was missing a 'target' character.")
            return "Failure: You need to specify who you want to talk to."
            
        npc = game_state.find_character_in_location(target_name, world)
        if not npc:
            logging.info(f"Player tried to talk to '{target_name}', but they were not found.")
            return f"Failure: You don't see '{target_name}' here."
        
        topic = intent_data.get("topic")
        if not topic:
            # If AI doesn't identify a specific topic, it's a general greeting.
            topic = f"The player greets {npc.name}."
            logging.info(f"Player initiated general dialogue with '{npc.name}'.")
        else:
            logging.info(f"Player initiated dialogue with '{npc.name}' about '{topic}'.")

        # This part assumes a new function exists in AIManager: generate_dialogue_response
        # It's responsible for generating the NPC's actual spoken lines.
        # This keeps the AI logic neatly within the AIManager.
        dialogue_response = ai_manager.generate_dialogue_response(
            game_state=game_state,
            world=world,
            npc=npc,
            topic=topic
        )

        if dialogue_response:
            # The narration from the main loop will describe the action, 
            # and we inject the NPC's response directly into it.
            return f"Success: Dialogue - {dialogue_response}"
        else:
            logging.error(f"AI failed to generate dialogue response for NPC '{npc.name}'.")
            return "Failure: They don't seem to respond."