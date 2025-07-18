import logging
from typing import Dict, Any

from definitions.quests import Quest, Objective
from game_state import GameState
from display_manager import DisplayManager

class QuestManager:

    def start_quest(self, game_state: GameState, quest_data: Dict[str, Any], display: DisplayManager):
        quest_id = quest_data.get("id")
        if not quest_id or quest_id in game_state.quest_log:
            logging.warning(f"Attempted to start duplicate or invalid quest: {quest_id}")
            return

        objectives = [Objective(**obj_data) for obj_data in quest_data.get("objectives", [])]
        
        new_quest = Quest(
            id=quest_id,
            name=quest_data.get("name", "Unnamed Quest"),
            description=quest_data.get("description", ""),
            objectives=objectives
        )
        
        game_state.quest_log[quest_id] = new_quest
        logging.info(f"Quest '{new_quest.name}' started for player.")
        display.show_quest_started(new_quest.name, new_quest.description)

    def check_for_updates(self, game_state: GameState, intent: str, result: str, intent_data: Dict[str, Any], display: DisplayManager):
        if "Success" not in result and "Victory" not in result:
            return 

        for quest in game_state.quest_log.values():
            if quest.status != "active":
                continue
            
            needs_completion_check = False
            for objective in quest.objectives:
                if objective.is_complete:
                    continue
                
                was_updated = self._check_objective(objective, intent, result, intent_data, game_state, display)
                if was_updated:
                    needs_completion_check = True

            if needs_completion_check:
                if all(obj.is_complete for obj in quest.objectives):
                    self._complete_quest(quest, display)

    def _check_objective(self, objective: Objective, intent: str, result: str, intent_data: Dict[str, Any], game_state: GameState, display: DisplayManager) -> bool:
        
        target_match = False

        if objective.type == "acquire_item" and intent == "take_item":
            item_name = intent_data.get("target")
            if item_name and objective.target.lower() in item_name.lower():
                target_match = True

        elif objective.type == "kill_target" and result == "Victory":
            if game_state.combat_state and objective.target in game_state.combat_state.get("participants", []):
                 target_match = True

        elif objective.type == "reach_location" and intent == "move":
            if game_state.current_location_id == objective.target:
                target_match = True

        elif objective.type == "give_item" and intent == "give_item":
            item_name = intent_data.get("target")
            recipient_name = intent_data.get("recipient")
            required_recipient = objective.details.get("recipient")
            if (item_name and objective.target.lower() in item_name.lower() and
                recipient_name and required_recipient and required_recipient.lower() in recipient_name.lower()):
                 target_match = True

        if target_match:
            objective.current_count += 1
            if objective.current_count >= objective.required_count:
                objective.is_complete = True
                logging.info(f"Quest '{objective.id}' objective completed.")
                display.show_objective_complete(objective.description)
                return True
        
        return False

    def _complete_quest(self, quest: Quest, display: DisplayManager):
        quest.status = "completed"
        logging.info(f"Quest '{quest.name}' has been completed by the player.")
        display.show_quest_complete(quest.name)