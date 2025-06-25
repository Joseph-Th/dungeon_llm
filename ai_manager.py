import google.generativeai as genai
import json
import logging
from typing import Optional, Dict, Any

from config import GEMINI_API_KEY
from prompts import INFERENCE_PROMPT, MECHANICS_PROMPT, NARRATION_PROMPT
from game_state import GameState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AIManager:
    def __init__(self):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
            logging.info("AIManager initialized successfully.")
        except Exception as e:
            logging.critical(f"Failed to configure Gemini API. Is the API key valid? Error: {e}")
            raise

    def _execute_prompt(self, prompt: str, expect_json: bool = True) -> Optional[Dict[str, Any] | str]:
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()

            if not expect_json:
                return raw_text

            cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            if not cleaned_text:
                logging.warning("Received empty response from API.")
                return None

            parsed_json = json.loads(cleaned_text)
            return parsed_json

        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from API response. Raw text: '{raw_text}'")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during API call: {e}")
            return None

    def get_player_intent(self, game_state: GameState, user_input: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Phase 1: Inferring intent for input: '{user_input}'")
        prompt = INFERENCE_PROMPT.format(
            game_state=game_state.get_context_string(),
            player_input=user_input
        )
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            return result
        return None

    def determine_skill_check_details(self, game_state: GameState, action_description: str) -> Optional[Dict[str, Any]]:
        logging.info(f"Phase 2: Determining mechanics for action: '{action_description}'")
        prompt = MECHANICS_PROMPT.format(
            game_state=game_state.get_context_string(),
            action_description=action_description
        )
        result = self._execute_prompt(prompt, expect_json=True)
        if isinstance(result, dict):
            return result
        return None

    def narrate_outcome(self, game_state: GameState, action_description: str, result: str) -> str:
        logging.info(f"Phase 3: Narrating outcome for result: '{result}'")
        prompt = NARRATION_PROMPT.format(
            game_state=game_state.get_context_string(),
            action_description=action_description,
            result=result
        )
        narration = self._execute_prompt(prompt, expect_json=False)
        if isinstance(narration, str) and narration:
            return narration
        return "The world seems to pause for a moment, unsure how to react. Perhaps try something else?"