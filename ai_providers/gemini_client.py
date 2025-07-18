# ai_providers/gemini_client.py
import google.generativeai as genai
import logging

from config import GEMINI_API_KEY, MODEL_NAME

class GeminiClient:
    """A client for interacting with the Google Gemini API."""

    def __init__(self):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(MODEL_NAME)
            logging.info(f"GeminiClient initialized successfully with model '{MODEL_NAME}'.")
        except Exception as e:
            logging.critical(f"Failed to configure GeminiClient. Is the API key valid? Error: {e}")
            raise

    def generate_content(self, prompt: str) -> str:
        """
        Generates content using the Gemini API.
        
        Args:
            prompt: The full prompt to send to the API.

        Returns:
            The raw text response from the API.

        Raises:
            Exception: Propagates any exception from the genai library call.
        """
        logging.info("Calling Gemini API...")
        response = self.model.generate_content(prompt)
        return response.text