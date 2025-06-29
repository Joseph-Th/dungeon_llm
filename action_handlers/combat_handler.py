import logging
import random
from typing import Dict, Any, TYPE_CHECKING, List, Optional

from definitions.entities import Character
from game_state import GameState, GameWorld

if TYPE_CHECKING:
    from ai_manager import AIManager

class CombatHandler:

    def process_combat_intent(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        intent = intent_data.get("intent")

        if not game_state.combat_state and intent == "attack":
            return self._initiate_combat(game_state, world, ai_manager, intent_data)

        if game_state.combat_state:
            active_char_name = game_state.combat_state["participants"][game_state.combat_state["turn_index"]]
            if active_char_name != game_state.player.name:
                logging.error("Received player combat intent when it was not the player's turn.")
                return f"Failure: It is not your turn. {active_char_name} is acting."

            if intent == "attack":
                target_name = intent_data.get("target")
                if not target_name:
                    return "Failure: You must specify a target to attack."

                participants = self._get_combat_participants(game_state, world)
                target = next((p for p in participants if p.name.lower() == target_name.lower() and p != game_state.player), None)
                if not target:
                    return f"Failure: '{target_name}' is not in this fight."

                attack_narration = self._execute_attack(game_state, game_state.player, target)
                game_state.combat_state["turn_index"] += 1
                return self._run_combat_loop(game_state, world, ai_manager, initial_narration=attack_narration)
            
            return "Failure: That is not a valid action in combat."

        logging.warning(f"CombatHandler received an unhandled intent: {intent}")
        return "Failure: You can't do that right now."

    def _initiate_combat(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict[str, Any]) -> str:
        target_name = intent_data.get("target")
        if not target_name:
            return "Failure: Who are you trying to attack?"

        target = game_state.find_character_in_location(target_name, world)
        if not target:
            return f"Failure: You don't see '{target_name}' here."

        if target == game_state.player:
            return "Failure: You decide against attacking yourself."

        logging.info(f"Combat initiated by player against '{target.name}'.")

        location = game_state.get_current_location(world)
        if not location:
            logging.error("Cannot initiate combat in a non-existent location.")
            return "Failure: You cannot fight in the void."

        initial_participants = [game_state.player] + [char for char in location.characters if char.is_hostile or char == target]
        for p in initial_participants:
            p.is_hostile = True

        turn_order = sorted(initial_participants, key=lambda x: random.randint(1, 20) + (x.stats.get("dexterity", 10) - 10) // 2, reverse=True)

        game_state.combat_state = {
            "participants": [p.name for p in turn_order],
            "turn_index": 0,
            "round_count": 1
        }
        
        initial_narration = f"You draw your weapon and attack {target.name}! Combat has begun."
        attack_narration = self._execute_attack(game_state, game_state.player, target)

        game_state.combat_state["turn_index"] += 1
        return self._run_combat_loop(game_state, world, ai_manager, initial_narration=f"{initial_narration}\n{attack_narration}")

    def _get_combat_participants(self, game_state: GameState, world: GameWorld) -> List[Character]:
        if not game_state.combat_state:
            return []

        location = game_state.get_current_location(world)
        if not location:
            return []

        participant_names = game_state.combat_state.get("participants", [])
        all_chars = [game_state.player] + location.characters
        
        participant_objects = []
        for name in participant_names:
            found_char = next((char for char in all_chars if char.name == name), None)
            if found_char:
                participant_objects.append(found_char)
        
        return participant_objects

    def _run_combat_loop(self, game_state: GameState, world: GameWorld, ai_manager: 'AIManager', initial_narration: str = "") -> str:
        narration_log = [initial_narration] if initial_narration else []

        while game_state.combat_state:
            end_state = self._check_combat_end(game_state, world)
            if end_state:
                game_state.combat_state = None
                narration_log.append(end_state)
                return "\n".join(filter(None, narration_log))

            turn_index = game_state.combat_state["turn_index"]
            participant_names = game_state.combat_state["participants"]
            
            if turn_index >= len(participant_names):
                game_state.combat_state["turn_index"] = 0
                game_state.combat_state["round_count"] += 1
                narration_log.append(f"--- Round {game_state.combat_state['round_count']} ---")
                continue

            participants = self._get_combat_participants(game_state, world)
            if not participants:
                game_state.combat_state = None
                return "Victory: The last foe falls, and the dust settles."
            
            attacker = participants[turn_index]
            
            if attacker.hp <= 0:
                game_state.combat_state["turn_index"] += 1
                continue

            if attacker == game_state.player:
                narration_log.append("It is your turn to act.")
                return "\n".join(filter(None, narration_log))
            else:
                npc_action = self._get_npc_combat_action(attacker, game_state, world, ai_manager)
                
                if npc_action and npc_action.get("action") == "attack":
                    target_name = npc_action.get("target")
                    target = game_state.player if target_name == game_state.player.name else None
                    if target:
                        narration_log.append(self._execute_attack(game_state, attacker, target))
                else:
                    narration_log.append(f"{attacker.name} hesitates, unsure what to do.")
            
            game_state.combat_state["turn_index"] += 1
        
        return "\n".join(filter(None, narration_log))

    def _get_npc_combat_action(self, npc: Character, game_state: GameState, world: GameWorld, ai_manager: 'AIManager') -> Dict[str, Any]:
        logging.info(f"Getting combat action for NPC '{npc.name}'.")
        return {
            "action": "attack",
            "target": game_state.player.name
        }

    def _execute_attack(self, game_state: GameState, attacker: Character, target: Character) -> str:
        def get_attack_roll(char: Character) -> int:
            modifier = (char.stats.get("strength", 10) - 10) // 2 + char.get_total_attack_bonus()
            return random.randint(1, 20) + modifier
        
        def get_damage_amount(char: Character) -> int:
            dice_str = char.get_damage_dice()
            num_dice, dice_size = map(int, dice_str.split('d'))
            return sum(random.randint(1, dice_size) for _ in range(num_dice))

        attack_roll = get_attack_roll(attacker)
        target_ac = target.get_total_armor_class()

        if attack_roll >= target_ac:
            damage = get_damage_amount(attacker)
            target.hp -= damage
            logging.info(f"HIT! {attacker.name} attacks {target.name} for {damage} damage. {target.name} HP: {target.hp}/{target.max_hp}")
            
            narration = f"{attacker.name}'s attack hits {target.name} for {damage} damage!"
            if target.hp <= 0:
                narration += f" {target.name} collapses, defeated!"
                if game_state.combat_state:
                    self._remove_defeated_participant(character=target, game_state=game_state)
            return narration
        else:
            logging.info(f"MISS! {attacker.name} attacks {target.name} but fails to hit.")
            return f"{attacker.name} attacks {target.name} but misses."

    def _check_combat_end(self, game_state: GameState, world: GameWorld) -> Optional[str]:
        participants = self._get_combat_participants(game_state, world)
        
        if game_state.player.hp <= 0:
            return "Defeat: You have been vanquished."

        living_opponents = [p for p in participants if p != game_state.player and p.hp > 0]
        if not living_opponents:
            return "Victory: The last of your foes has been defeated!"
        
        return None
    
    def _remove_defeated_participant(self, character: Character, game_state: GameState):
        if game_state.combat_state and character.name in game_state.combat_state["participants"]:
            current_turn_index = game_state.combat_state["turn_index"]
            defeated_char_index = -1
            try:
                defeated_char_index = game_state.combat_state["participants"].index(character.name)
            except ValueError:
                logging.warning(f"Tried to remove defeated participant '{character.name}' who was already removed.")
                return

            game_state.combat_state["participants"].remove(character.name)
            
            if defeated_char_index < current_turn_index:
                game_state.combat_state["turn_index"] -= 1