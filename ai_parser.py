import json
import logging
import re
from typing import Optional, Dict, Any

class AIParser:
    """A dedicated class for cleaning and parsing raw text output from AI models."""

    def find_and_parse_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Finds the first valid JSON object in a raw string and parses it.
        
        Args:
            raw_text: The potentially messy string from the AI.

        Returns:
            A parsed dictionary, or None if no valid JSON is found.
        """
        if not isinstance(raw_text, str):
            return None

        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            json_string = match.group(0)
            try:
                return json.loads(json_string)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to decode extracted JSON. Error: {e}. String was: '{json_string}'")
                return None
        else:
            logging.warning(f"Could not find any JSON-like structure in raw text: '{raw_text}'")
            return None

    def parse_simple_response(self, raw_text: str) -> Optional[str]:
        """
        Cleans and returns a simple, single-line text response from the AI.
        Strips common markdown and returns None if the result is empty or the word 'None'.
        
        Args:
            raw_text: The potentially messy string from the AI.

        Returns:
            A cleaned string, or None.
        """
        if not isinstance(raw_text, str):
            return None
        
        # Remove markdown code blocks and then strip specific markdown characters
        cleaned_response = raw_text.replace("```json", "").replace("```", "").strip()
        cleaned_response = cleaned_response.strip().strip('`').strip('*').strip('"').strip()

        if cleaned_response.lower() == "none" or not cleaned_response:
            return None
        
        return cleaned_response