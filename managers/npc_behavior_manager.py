import logging
from typing import List, Dict, Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game_state import GameState, GameWorld
    from ai_manager import AIManager
    from definitions.entities import Character
    from definitions.world_objects import Location

class NPCBehaviorManager:

    def __init__(self):
        logging.info("NPCBehaviorManager initialized.")
        self.cooldowns: Dict[str, int] = {}

    def update_behaviors(self, game_state: 'GameState', world: 'GameWorld', ai_manager: 'AIManager') -> List[Dict[str, Any]]:
        mutations = []
        
        current_location = game_state.get_current_location(world)
        if not current_location:
            return []

        if game_state.combat_state:
            mutations.extend(self._handle_combat_reactions(game_state, world, current_location))
        
        return mutations

    def _handle_combat_reactions(self, game_state: 'GameState', world: 'GameWorld', location: 'Location') -> List[Dict[str, Any]]:
        mutations = []
        if not game_state.combat_state:
            return mutations

        for character in location.characters:
            if character.name in game_state.combat_state["participants"]:
                continue

            if self._is_on_cooldown(character.name):
                continue

            if "coward" in character.personality_tags:
                flee_mutation = self._flee_combat(character, location, world)
                if flee_mutation:
                    mutations.append(flee_mutation)
                    self.set_cooldown(character.name, game_state.turn_count, 10)

        return mutations

    def _flee_combat(self, character: 'Character', location: 'Location', world: 'GameWorld') -> Optional[Dict[str, Any]]:
        if not location.exits:
            logging.info(f"NPC '{character.name}' wants to flee but has no exits.")
            return None

        flee_exit_id = next(iter(location.exits.values()))
        
        destination = world.get_location(flee_exit_id)
        if destination:
            logging.info(f"NPC '{character.name}' is fleeing from '{location.id}' to '{flee_exit_id}'.")
            return {
                "op": "move_npc",
                "character_name": character.name,
                "new_location_id": flee_exit_id
            }
        return None

    def _is_on_cooldown(self, character_name: str) -> bool:
        return character_name in self.cooldowns

    def set_cooldown(self, character_name: str, current_turn: int, duration: int):
        logging.info(f"Setting action cooldown for NPC '{character_name}'.")
        pass