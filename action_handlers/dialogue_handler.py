import logging
from typing import Dict, Any, TYPE_CHECKING

from game_state import GameState, GameWorld, Character
from game_mechanics import perform_skill_check
from definitions.quests import Quest

if TYPE_CHECKING:
    from ai_manager import AIManager

class DialogueHandler:

    def _get_quest_from_location(self, quest_id: str, location: Any) -> Quest | None:
        if not location:
            return None
        return location.get_quest_by_id(quest_id)

    def _handle_work_inquiry(self, game_state: GameState, world: GameWorld, npc: Character) -> str:
        current_location = game_state.get_current_location(world)
        if not current_location or not npc.available_quest_ids:
            logging.info(f"NPC '{npc.name}' has no available quests.")
            return "The player is asking for work, but you have none to offer. Politely tell them you don't have any jobs right now."

        quest_id_to_offer = npc.available_quest_ids[0]
        quest_to_offer = self._get_quest_from_location(quest_id_to_offer, current_location)

        if not quest_to_offer:
            logging.error(f"NPC '{npc.name}' has quest ID '{quest_id_to_offer}' but it was not found in location '{current_location.id}'.")
            return "You had a job in mind, but the details seem to have slipped your mind. You tell the player to check back later."

        passed_check = True
        if quest_to_offer.required_stat and quest_to_offer.required_dc > 0:
            logging.info(f"Quest '{quest_to_offer.name}' requires a check: {quest_to_offer.required_stat} DC {quest_to_offer.required_dc}.")
            passed_check = perform_skill_check(game_state.player, quest_to_offer.required_stat, quest_to_offer.required_dc)

        if passed_check:
            logging.info("Player passed the stat check. NPC will offer the quest.")
            return f"The player seems capable. You should offer them the '{quest_to_offer.name}' quest and describe it."
        else:
            logging.info("Player failed the stat check. NPC will refuse to offer the quest.")
            return f"The player does not seem capable enough for the '{quest_to_offer.name}' quest. Politely tell them they aren't the right fit."

    def _handle_action_request(self, game_state: GameState, world: GameWorld, npc: Character, topic: str) -> str:
        parts = topic.split(':')
        if len(parts) < 3:
            return "Failure: The request was unclear."

        action = parts[1]
        action_target_name = parts[2]

        if action == "unlock":
            if npc.mood in ['friendly', 'grateful', 'impressed']:
                target_obj = game_state.find_interactable_in_location(action_target_name, world)
                if target_obj and "locked" in target_obj.state:
                    if target_obj.state["locked"]:
                        logging.info(f"NPC '{npc.name}' is willing and able to unlock '{target_obj.name}'.")
                        target_obj.state["locked"] = False
                        return f"Success: Dialogue - {npc.name} nods. 'Of course.' He walks over and unlocks the {target_obj.name} with a click."
                    else:
                        return f"Success: Dialogue - {npc.name} looks at the {target_obj.name} and says, 'It's already unlocked.'"
                else:
                    return f"Success: Dialogue - {npc.name} looks confused and says, 'I can't seem to find a {action_target_name} to unlock.'"
            else:
                logging.info(f"NPC '{npc.name}' is not friendly enough to fulfill the request.")
                return f"Success: Dialogue - {npc.name} scoffs, 'And why would I do that for you?'"
        
        return "Failure: The NPC doesn't know how to do that."

    def process_dialogue_intent(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        target_name = intent_data.get("target")
        if not target_name:
            logging.warning("Dialogue intent was missing a 'target' character.")
            return "Failure: You need to specify who you want to talk to."
            
        npc = game_state.find_character_in_location(target_name, world)
        if not npc:
            logging.info(f"Player tried to talk to '{target_name}', but they were not found.")
            return f"Failure: You don't see '{target_name}' here."
        
        topic = intent_data.get("topic", "").lower()
        final_topic = topic

        if topic.startswith("request:"):
            return self._handle_action_request(game_state, world, npc, topic)

        is_asking_for_work = any(keyword in topic for keyword in ["work", "job", "task", "quest"])
        if is_asking_for_work:
            final_topic = self._handle_work_inquiry(game_state, world, npc)

        dialogue_response = ai_manager.generate_dialogue_response(
            game_state=game_state,
            world=world,
            npc=npc,
            topic=final_topic
        )

        if dialogue_response:
            return f"Success: Dialogue - {dialogue_response}"
        else:
            logging.error(f"AI failed to generate dialogue response for NPC '{npc.name}'.")
            return "Failure: They don't seem to respond."