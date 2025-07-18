import requests
import logging
from typing import Optional

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

class OllamaClient:

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.timeout = OLLAMA_TIMEOUT
        logging.info(f"OllamaClient initialized for model '{self.model}' at '{self.base_url}' with a timeout of {self.timeout} seconds.")

    def generate_content(self, prompt: str, force_json: bool) -> Optional[str]:
        logging.info(f"Calling Ollama API with model '{self.model}' (JSON Mode: {force_json})...")
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            if force_json:
                payload["format"] = "json"

            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            response_json = response.json()
            return response_json.get("response")

        except requests.exceptions.Timeout:
            logging.error(f"Ollama call timed out after {self.timeout} seconds. The local model may be unresponsive or the task is too complex for the current hardware.")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to connect to Ollama at '{self.base_url}'. Error: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during Ollama call: {e}")
            return None