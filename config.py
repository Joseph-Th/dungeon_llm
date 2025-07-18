# config.py

# --- Primary API Configuration ---
# Set to False to disable the Gemini API and use the Ollama fallback directly.
USE_GEMINI_API = False

# --- Gemini API Configuration ---
# Your Gemini key here...
GEMINI_API_KEY = "AIzaSyA0BM8H6zh-LSWootFH_Subnur7bPQk_cs"

# --- Game Configuration ---
MODEL_NAME = "gemini-1.5-flash"


# --- Ollama Fallback Configuration ---
OLLAMA_ENABLED = True
OLLAMA_BASE_URL = "http://localhost:11434"

# The name of the Ollama model to use. After testing, llama3 proved more reliable
# at understanding intent than qwen for this specific application.
OLLAMA_MODEL = "llama3:8b"

# The number of seconds to wait for a response from the Ollama API before giving up.
# We are keeping the longer timeout as it's a good general robustness improvement.
OLLAMA_TIMEOUT = 45