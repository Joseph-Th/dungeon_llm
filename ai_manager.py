import json
import logging
from typing import Optional, Dict, Any

from config import OLLAMA_ENABLED, USE_GEMINI_API
from prompts import (
    MECHANICS_PROMPT,
    NARRATION_PROMPT,
    LOCATION_GENERATION_PROMPT,
    NPC_STATE_UPDATE_PROMPT,
    WORLD_EVENT_PROMPT,
    DIALOGUE_GENERATION_PROMPT,
    QUEST_GENERATION_PROMPT
)
from prompts.decomposition import (
    GET_INTENT_PROMPT,
    GET_TARGET_PROMPT,
    GET_DIALOGUE_TOPIC_PROMPT,
    GET_RECIPIENT_PROMPT,
    GET_TARGET_ON_PROMPT,
    GET_ACTION_DESCRIPTION_PROMPT,
    GET_MOVE_DESTINATION_PROMPT,
    GET_QUEST_ACTION_TYPE_PROMPT
)
from game_state import GameState, GameWorld, Location, Character
from ai_providers.gemini_client import GeminiClient
from ai_providers.ollama_client import OllamaClient
from ai_parser import AIParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AIManager:

    def __init__(self):
        self.gemini_client = GeminiClient() if USE_GEMINI_API else None
        self.ollama_client = OllamaClient() if OLLAMA_ENABLED else None
        self.parser = AIParser()

        if not self.ollama_client:
            raise RuntimeError("Ollama is not enabled, but is required as the default provider.")

        logging.info("AIManager initialized. Default provider: Ollama. Gemini is available for specialized tasks.")

    def _generate_content(self, prompt: str, expect_json: bool) -> Optional[str]:
        # Guard Clause to satisfy Pylance and prevent runtime errors.
        if not self.ollama_client:
            logging.critical("Ollama client is not available to generate content.")
            return None
            
        return self.ollama_client.generate_content(prompt, force_json=expect_json)

    def _execute_prompt(self, prompt: str, expect_json: bool = True) -> Optional[Dict[str, Any] | str]:
        raw_text = self._generate_content(prompt, expect_json=expect_json)
        if raw_text is None:
            return None

        logging.info(f"Received raw response from AI provider: {raw_text.strip()}")

        if expect_json:
            return self.parser.find_and_parse_json(raw_text)
        else:
            return self.parser.parse_simple_response(raw_text)

    def _get_simple_response(self, prompt: str) -> Optional[str]:
        response = self._execute_prompt(prompt, expect_json=False)
        if isinstance(response, str):
            return response
        return None

    def get_player_intent(self, game_state: GameState, world: GameWorld, user_input: str) -> Optional[Dict[str, Any]]:
        logging.info("--- Starting Intent Assembly Line ---")

        logging.info("Station 1: Classifying Intent...")
        intent_prompt = GET_INTENT_PROMPT.format(user_input=user_input)
        intent = self._get_simple_response(intent_prompt)
        if not intent:
            logging.error("Assembly line failed at Station 1: Could not determine intent.")
            return None
        logging.info(f"-> Determined Intent: '{intent}'")

        logging.info("Station 2: Identifying Target...")
        current_loc = game_state.get_current_location(world)
        character_names = [c.name for c in current_loc.characters] if current_loc else []
        item_names = [i.name for i in current_loc.items] if current_loc else []
        interactable_names = [i.name for i in current_loc.interactables] if current_loc else []
        exit_descriptions = list(current_loc.exits.keys()) if current_loc else []
        
        target_prompt = GET_TARGET_PROMPT.format(
            user_input=user_input,
            character_names=character_names,
            item_names=item_names,
            interactable_names=interactable_names,
            exit_descriptions=exit_descriptions
        )
        target = self._get_simple_response(target_prompt)
        logging.info(f"-> Determined Target: '{target}'")

        if intent == "move":
            logging.info("Special Station 'move': Determining Destination ID...")
            move_prompt = GET_MOVE_DESTINATION_PROMPT.format(
                user_input=user_input,
                exits_json=json.dumps(current_loc.exits, indent=2) if current_loc else "{}"
            )
            destination_id = self._get_simple_response(move_prompt)
            if destination_id and destination_id in (current_loc.exits.values() if current_loc else []):
                target = destination_id
                logging.info(f"-> Overrode target with Destination ID: '{target}'")
            else:
                logging.warning(f"Could not reliably determine destination ID for move. Sticking with general target: '{target}'")

        logging.info("Station 3: Extracting Additional Parameters...")
        parameters = {}
        if intent == "dialogue":
            topic_prompt = GET_DIALOGUE_TOPIC_PROMPT.format(user_input=user_input)
            topic = self._get_simple_response(topic_prompt)
            if topic: parameters['topic'] = topic
        elif intent == "quest_action":
            action_type_prompt = GET_QUEST_ACTION_TYPE_PROMPT.format(user_input=user_input)
            action_type = self._get_simple_response(action_type_prompt)
            if action_type: parameters['action_type'] = action_type
        elif intent == "give_item":
            recipient_prompt = GET_RECIPIENT_PROMPT.format(user_input=user_input)
            recipient = self._get_simple_response(recipient_prompt)
            if recipient: parameters['recipient'] = recipient
        elif intent == "use_item":
            target_on_prompt = GET_TARGET_ON_PROMPT.format(user_input=user_input)
            target_on = self._get_simple_response(target_on_prompt)
            if target_on: parameters['target_on'] = target_on
        logging.info(f"-> Found Parameters: {parameters}")
        
        logging.info("Foreman: Assembling Final Intent Data...")
        action_desc_prompt = GET_ACTION_DESCRIPTION_PROMPT.format(
            user_input=user_input,
            intent=intent,
            target=target
        )
        action_description = self._get_simple_response(action_desc_prompt) or f"Player action: {user_input}"

        intent_data = {
            "intent": intent,
            "target": target,
            "action_description": action_description
        }
        intent_data.update(parameters)
        intent_data = {k: v for k, v in intent_data.items() if v is not None}
        
        logging.info(f"--- Assembly Line Complete. Final Data: {intent_data} ---")
        return intent_data

    def determine_skill_check_details(self, game_state: GameState, world: GameWorld, action_description: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Phase 2: Determining mechanics for action: '{action_description}'")
        context_str = game_state.get_context_string(world)
        prompt = f"{MECHANICS_PROMPT}\n\nHere is the current game state for context:\n{context_str}\n\nHere is the player's described action:\n\"{action_description}\""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            return result
        return None

    def generate_quest_from_context(self, quest_giver: Character, offer_memory: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Generating quest from NPC '{quest_giver.name}' based on memory: '{offer_memory}'.")
        prompt = f"{QUEST_GENERATION_PROMPT}\n\nCONTEXT:\n- Quest Giver Name: \"{quest_giver.name}\"\n- The quest giver's memory of the offer: \"{offer_memory}\""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            logging.info(f"Successfully generated JSON data for new quest from '{quest_giver.name}'.")
            return result
        logging.error(f"Failed to generate valid JSON for quest from '{quest_giver.name}'.")
        return None

    def generate_new_location(self, source_location: Location, exit_description: str, new_location_id: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Dynamically generating new location '{new_location_id}' from source '{source_location.id}'.")
        prompt = f"{LOCATION_GENERATION_PROMPT}\n\nHere is the context for the new location to generate:\n- The player is coming from a location named: \"{source_location.name}\" (ID: {source_location.id})\n- The exit they used was described as: \"{exit_description}\"\n- The required unique ID for this new location must be: \"{new_location_id}\""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            logging.info(f"Successfully generated JSON data for new location '{new_location_id}'.")
            return result
        logging.error(f"Failed to generate valid JSON for new location '{new_location_id}'.")
        return None

    def narrate_outcome(self, game_state: GameState, world: GameWorld, action_description: str, result: str) -> str:
        logging.info(f"Phase 3: Narrating outcome for result: '{result}'")
        context_str = game_state.get_context_string(world)
        prompt = f"{NARRATION_PROMPT}\n\nHere is the current game state for context:\n{context_str}\n\nHere is what the player tried to do:\n\"{action_description}\"\n\nHere is the result of their attempt: {result}"
        narration = self._execute_prompt(prompt, expect_json=False)
        if isinstance(narration, str) and narration:
            return narration
        return "The world seems to pause for a moment, unsure how to react. Perhaps try something else?"

    def generate_dialogue_response(self, game_state: GameState, world: GameWorld, npc: Character, topic: str) -> Optional[str]:
        logging.info(f"Generating dialogue for NPC '{npc.name}' on topic: '{topic}'")
        context_str = game_state.get_context_string(world)
        prompt = f"{DIALOGUE_GENERATION_PROMPT}\n\nCONTEXT:\n- Current Game State: {context_str}\n- NPC being spoken to: {json.dumps(npc.to_dict(), indent=2)}\n- Player's action/topic of conversation: \"{topic}\""
        narration = self._execute_prompt(prompt, expect_json=False)
        if isinstance(narration, str) and narration:
            return narration.strip('"')
        return None

    def update_npc_state(self, npc: Character, action_description: str, narration: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Phase 4: Updating state for NPC '{npc.name}'.")
        npc_state_json = json.dumps(npc.to_dict(), indent=2)
        prompt = f"{NPC_STATE_UPDATE_PROMPT}\n\nCONTEXT:\n- Current NPC State: {npc_state_json}\n- Player's Action: \"{action_description}\"\n- Interaction Outcome (Narration): \"{narration}\""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            return result
        return None

    def generate_world_event(self, game_state: GameState, world: GameWorld) -> Optional[Dict[str, Any]]:
        logging.info("Checking for a background world event...")
        context_str = game_state.get_context_string(world)
        prompt = f"{WORLD_EVENT_PROMPT}\n\nHere is the current game state for context:\n{context_str}"
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict) and result:
            return result
        return None