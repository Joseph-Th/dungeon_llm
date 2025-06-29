import google.generativeai as genai
import json
import logging
from typing import Optional, Dict, Any

from config import GEMINI_API_KEY, MODEL_NAME
from prompts import (
    INFERENCE_PROMPT, 
    MECHANICS_PROMPT, 
    NARRATION_PROMPT, 
    LOCATION_GENERATION_PROMPT,
    NPC_STATE_UPDATE_PROMPT,
    WORLD_EVENT_PROMPT,
    DIALOGUE_GENERATION_PROMPT,
    QUEST_GENERATION_PROMPT
)
from game_state import GameState, GameWorld, Location, Character

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AIManager:
    def __init__(self):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(MODEL_NAME)
            logging.info(f"AIManager initialized successfully with model '{MODEL_NAME}'.")
        except Exception as e:
            logging.critical(f"Failed to configure Gemini API. Is the API key valid? Error: {e}")
            raise

    def _execute_prompt(self, prompt: str, expect_json: bool = True) -> Optional[Dict[str, Any] | str]:
        response = None
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()

            if not expect_json:
                return raw_text

            cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()
            if not cleaned_text:
                logging.warning("Received empty response from API.")
                return None
            
            return json.loads(cleaned_text)

        except json.JSONDecodeError as e:
            error_text = response.text if response else "N/A"
            logging.error(f"Failed to decode JSON from API response. Error: {e}. Raw text was: '{error_text}'")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during API call: {e}")
            return None

    def get_player_intent(self, game_state: GameState, world: GameWorld, user_input: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Phase 1: Inferring intent for input: '{user_input}'")
        context_str = game_state.get_context_string(world)
        
        prompt = f"""{INFERENCE_PROMPT}

Here is the current game state for context:
{context_str}

Here is the player's command:
"{user_input}"
"""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            return result
        return None

    def determine_skill_check_details(self, game_state: GameState, world: GameWorld, action_description: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Phase 2: Determining mechanics for action: '{action_description}'")
        context_str = game_state.get_context_string(world)

        prompt = f"""{MECHANICS_PROMPT}

Here is the current game state for context:
{context_str}

Here is the player's described action:
"{action_description}"
"""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            return result
        return None
        
    def generate_quest_from_context(self, quest_giver: Character, offer_memory: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Generating quest from NPC '{quest_giver.name}' based on memory: '{offer_memory}'.")
        
        prompt = f"""{QUEST_GENERATION_PROMPT}

CONTEXT:
- Quest Giver Name: "{quest_giver.name}"
- The quest giver's memory of the offer: "{offer_memory}"
"""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            logging.info(f"Successfully generated JSON data for new quest from '{quest_giver.name}'.")
            return result
        
        logging.error(f"Failed to generate valid JSON for quest from '{quest_giver.name}'.")
        return None


    def generate_new_location(self, source_location: Location, exit_description: str, new_location_id: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Dynamically generating new location '{new_location_id}' from source '{source_location.id}'.")

        prompt = f"""{LOCATION_GENERATION_PROMPT}

Here is the context for the new location to generate:
- The player is coming from a location named: "{source_location.name}" (ID: {source_location.id})
- The exit they used was described as: "{exit_description}"
- The required unique ID for this new location must be: "{new_location_id}"
"""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            logging.info(f"Successfully generated JSON data for new location '{new_location_id}'.")
            return result
        
        logging.error(f"Failed to generate valid JSON for new location '{new_location_id}'.")
        return None

    def narrate_outcome(self, game_state: GameState, world: GameWorld, action_description: str, result: str) -> str:
        logging.info(f"Phase 3: Narrating outcome for result: '{result}'")
        context_str = game_state.get_context_string(world)
        
        prompt = f"""{NARRATION_PROMPT}

Here is the current game state for context:
{context_str}

Here is what the player tried to do:
"{action_description}"

Here is the result of their attempt: {result}
"""
        narration = self._execute_prompt(prompt, expect_json=False)
        if isinstance(narration, str) and narration:
            return narration
        return "The world seems to pause for a moment, unsure how to react. Perhaps try something else?"
        
    def generate_dialogue_response(self, game_state: GameState, world: GameWorld, npc: Character, topic: str) -> Optional[str]:
        logging.info(f"Generating dialogue for NPC '{npc.name}' on topic: '{topic}'")
        
        context_str = game_state.get_context_string(world)

        prompt = f"""{DIALOGUE_GENERATION_PROMPT}
        
CONTEXT:
- Current Game State: {context_str}
- NPC being spoken to: {json.dumps(npc.to_dict(), indent=2)}
- Player's action/topic of conversation: "{topic}"
"""
        narration = self._execute_prompt(prompt, expect_json=False)
        if isinstance(narration, str) and narration:
            return narration.strip('"') 
        return None

    def update_npc_state(self, npc: Character, action_description: str, narration: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Phase 4: Updating state for NPC '{npc.name}'.")
        
        npc_state_json = json.dumps(npc.to_dict(), indent=2)

        prompt = f"""{NPC_STATE_UPDATE_PROMPT}

CONTEXT:
- Current NPC State: {npc_state_json}
- Player's Action: "{action_description}"
- Interaction Outcome (Narration): "{narration}"
"""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            return result
        return None

    def generate_world_event(self, game_state: GameState, world: GameWorld) -> Optional[Dict[str, Any]]:
        logging.info("Checking for a background world event...")
        context_str = game_state.get_context_string(world)
        
        prompt = f"""{WORLD_EVENT_PROMPT}

Here is the current game state for context:
{context_str}
"""
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict) and result:
            return result
        return None