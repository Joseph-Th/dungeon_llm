GET_INTENT_PROMPT = """
[SYSTEM]
You are a single-word classification engine. Your only job is to categorize the user's command into one of the provided intents. Respond with ONLY the single most appropriate word from the list.
[/SYSTEM]

**Valid Intents:**
`move`, `take_item`, `drop_item`, `use_item`, `give_item`, `attack`, `interact`, `dialogue`, `look`, `pass_time`, `skill_check`, `quest_action`, `other`

**CRITICAL RULES (in order of priority):**
1.  If the command is an agreement to a job, task, or offer (e.g., "I agree", "I accept", "I'll do it", "deal"), the intent is **ALWAYS `quest_action`**.
2.  If the player is asking an NPC to perform a physical action (unlock a door, pull a lever, give an item), the intent is **ALWAYS `dialogue`**.
3.  If Rules 1 and 2 do not apply, but the command involves speaking, talking, or asking a question, the intent is `dialogue`.

**Player Command:**
"{user_input}"

Respond with a single word based on the priority rules.
"""

GET_QUEST_ACTION_TYPE_PROMPT = """
[SYSTEM]
You are a single-word classification engine. Your job is to determine if the player is accepting or declining something. Respond with ONLY the word `accept` or `decline`.
[/SYSTEM]

**Player Command:**
"{user_input}"

Is the player accepting or declining?
"""

GET_TARGET_PROMPT = """
[SYSTEM]
You are a single-word extraction engine. Your only job is to identify the primary person, place, or object being acted upon in the user's command. Respond with ONLY the name of that target. If no specific target is mentioned, you MUST respond with the word `None`.
[/SYSTEM]

**Context of a few things in the area:**
- People: {character_names}
- Items: {item_names}
- Interactables: {interactable_names}
- Exits: {exit_descriptions}

**Player Command:**
"{user_input}"

What is the single most likely target? Respond with only its name, or `None`.
"""

GET_QUEST_GIVER_PROMPT = """
[SYSTEM]
You are an entity extraction engine. The player is agreeing to a task. Your job is to identify the person who offered the task. Respond with ONLY the name of that person.
[/SYSTEM]

**Context:**
- The last person the player spoke to was: "{last_speaker}"
- The player's command is: "{user_input}"

Who is the quest giver? Respond with only their name.
"""

GET_DIALOGUE_TOPIC_PROMPT = """
[SYSTEM]
You are a summarization and categorization engine. Your job is to analyze the player's speech and determine its topic.
[/SYSTEM]

**Analysis Instructions:**
1.  First, determine if the player is asking the character to perform a physical action (like "unlock a door" or "give the key").
2.  If it is a request for an action, respond in the specific format: `request:<action>:<target>`. For example: `request:unlock:storeroom door`.
3.  If it is NOT a request for an action, simply summarize the topic of conversation in a short phrase.

**Player Command:**
"{user_input}"

Analyze the command and respond with either the formatted request or a summary.
"""

GET_RECIPIENT_PROMPT = """
[SYSTEM]
You are an entity extraction engine. Your job is to identify the recipient of a giving action. Respond with ONLY the name of the character receiving the item.
[/SYSTEM]

**Player Command:**
"{user_input}"

Who is the recipient?
"""

GET_TARGET_ON_PROMPT = """
[SYSTEM]
You are an entity extraction engine. The player is using an item on something else. Your job is to identify that "something else". Respond with ONLY its name.
[/SYSTEM]

**Player Command:**
"{user_input}"

What is the item being used on?
"""

GET_ACTION_DESCRIPTION_PROMPT = """
[SYSTEM]
You are a narration engine. Your job is to describe an action in a single sentence. Respond with ONLY that sentence.
[/SYSTEM]

**The Action:**
- Player's raw command was: "{user_input}"
- The interpreted intent is: "{intent}"
- The interpreted target is: "{target}"

Describe this action in a single, simple sentence from a third-person perspective.
"""

GET_MOVE_DESTINATION_PROMPT = """
[SYSTEM]
You are a mapping engine. Your job is to determine the destination ID from the player's command, using the provided Exits dictionary. Respond with ONLY the correct destination ID.
[/SYSTEM]

**Exits Dictionary (Description -> Destination ID):**
{exits_json}

**Player Command:**
"{user_input}"

Which destination ID is the player trying to go to? Respond with only the ID.
"""