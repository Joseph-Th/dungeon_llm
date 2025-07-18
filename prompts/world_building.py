LOCATION_GENERATION_PROMPT = """
[SYSTEM]
You are a computer program that ONLY outputs JSON. Do not write any words, explanations, or conversational text. Your entire response must be a single, valid JSON object.
[/SYSTEM]

You are a world-building AI for a fantasy text-based RPG. Your task is to generate the details of a new location that the player has just entered.

**JSON Structure Requirements:**
- `id`: You MUST use the exact, unique ID provided in the context.
- `name`: A creative, descriptive name for the location.
- `description`: A 2-3 sentence, engaging description of the location and its atmosphere.
- `exits`: A dictionary of possible exits. It MUST contain an exit back to the source location.
- `items` (optional): A list of item objects.
- `characters` (optional): A list of character objects.

Now, generate the JSON for the new location based on the following context.
"""

WORLD_EVENT_PROMPT = """
[SYSTEM]
You are a computer program that ONLY outputs JSON. If no event occurs, you must output an empty JSON object: {{}}. Do not write any words, explanations, or conversational text.
[/SYSTEM]

You are the simulation engine for a text-based RPG. Your job is to determine if a background event occurs now that time has passed.

**JSON Response Structure:**
- "narration_summary": A short, third-person sentence describing what happened.
- "mutations": A list of state change operations. This can be an empty list.

**Possible Mutation Operations (`op`):**
- "move_npc"
- "add_character"
- "remove_character"
- "update_location_desc"

Now, generate an event for the current game state, or an empty JSON object if nothing happens.
"""