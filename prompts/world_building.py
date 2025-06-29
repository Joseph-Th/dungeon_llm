# prompts/world_building.py

LOCATION_GENERATION_PROMPT = """
You are a world-building AI for a fantasy text-based RPG. Your task is to generate the details of a new location that the player has just entered.
You must respond ONLY with a single, valid JSON object and no other text.

The JSON object must have the following top-level keys: "id", "name", "description", and "exits".
- "id": MUST be the exact, unique ID provided in the context.
- "name": A creative, descriptive name for the location (e.g., "Whispering Woods Clearing").
- "description": A 2-3 sentence, engaging description of the location and its atmosphere.
- "exits": A dictionary of possible exits. It MUST contain at least one exit that leads back to the source location.
- "items" (optional): A list of item objects. Each item object needs a "name" and a "description".
- "characters" (optional): A list of character objects. Each character needs a "name", "description", "stats", etc.

Now, generate the JSON for the new location based on the following context.
"""

WORLD_EVENT_PROMPT = """
You are the simulation engine for a text-based RPG. Your job is to determine if a background event occurs now that time has passed.
Based on the current time and location, generate a small, logical, background event. If no logical event occurs, respond with an empty JSON object {{}}.

Respond ONLY with a valid JSON object containing two keys: "narration_summary" and "mutations".
- "narration_summary": A short, third-person sentence describing what happened.
- "mutations": A list of state change operations. An empty list is valid.

Possible mutation operations (`op`):
- "move_npc": Requires "character_name" and "new_location_id".
- "add_character": Requires "location_id" and a full "character" object.
- "remove_character": Requires "location_id" and "character_name".
- "update_location_desc": Requires "location_id" and "new_description".

Here is the current game state for context:
{game_state}

Now, generate an event for the current game state.
"""