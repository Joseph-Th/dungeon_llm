import logging
from typing import List, Dict, Any, TYPE_CHECKING

from game_state import GameState, GameWorld, Character
from display_manager import DisplayManager

if TYPE_CHECKING:
    from ai_manager import AIManager
    from managers.npc_behavior_manager import NPCBehaviorManager
    from managers.weather_manager import WeatherManager
    from managers.companion_manager import CompanionManager

def execute_player_mutations(game_state: GameState, mutations: List[Dict[str, Any]]):
    for mutation in mutations:
        op = mutation.get("op")
        logging.info(f"Executing player mutation: {op}")
        try:
            if op == "damage_player":
                amount = mutation["amount"]
                game_state.player.hp -= amount
                logging.info(f"Player took {amount} damage. New HP: {game_state.player.hp}")
            elif op == "add_player_status":
                effect = mutation["effect"]
                if effect not in game_state.player.status_effects:
                    game_state.player.status_effects.append(effect)
                    logging.info(f"Player gained status effect: {effect}")
            elif op == "remove_player_status":
                effect = mutation["effect"]
                if effect in game_state.player.status_effects:
                    game_state.player.status_effects.remove(effect)
                    logging.info(f"Player lost status effect: {effect}")
        except (KeyError, TypeError) as e:
            logging.error(f"Invalid player mutation format for op '{op}'. Error: {e}. Mutation: {mutation}")

def execute_world_mutations(game_state: GameState, world: GameWorld, mutations: List[Dict[str, Any]]):
    for mutation in mutations:
        op = mutation.get("op")
        logging.info(f"Executing world event mutation: {op}")
        try:
            if op == "move_npc":
                char_name = mutation["character_name"]
                new_loc_id = mutation["new_location_id"]
                char_data = world.find_character_anywhere(char_name)
                new_loc = world.get_location(new_loc_id)
                if char_data and new_loc:
                    char, old_loc = char_data
                    if old_loc.id != new_loc.id:
                        old_loc.remove_character(char)
                        new_loc.add_character(char)
                        logging.info(f"Moved NPC '{char_name}' from '{old_loc.id}' to '{new_loc_id}'.")
            elif op == "add_character":
                loc_id = mutation["location_id"]
                loc = world.get_location(loc_id)
                if loc:
                    char_data = mutation["character"]
                    new_char = Character(**char_data)
                    loc.add_character(new_char)
            elif op == "remove_character":
                loc_id = mutation["location_id"]
                char_name = mutation["character_name"]
                loc = world.get_location(loc_id)
                if loc:
                    char_to_remove = next((c for c in loc.characters if c.name == char_name), None)
                    if char_to_remove:
                        loc.remove_character(char_to_remove)
                        logging.info(f"Removed NPC '{char_name}' from location '{loc_id}'.")
            elif op == "update_location_description":
                loc_id = mutation["location_id"]
                new_desc = mutation["new_description"]
                loc = world.get_location(loc_id)
                if loc:
                    loc.description = new_desc
                    logging.info(f"Updated description for location '{loc_id}'.")
            elif op == "add_exit":
                loc_id = mutation["location_id"]
                exit_desc = mutation["exit_description"]
                dest_id = mutation["destination_id"]
                loc = world.get_location(loc_id)
                if loc:
                    loc.exits[exit_desc] = dest_id
                    logging.info(f"Added exit from '{loc_id}' to '{dest_id}'.")
            elif op == "remove_exit":
                loc_id = mutation["location_id"]
                exit_desc = mutation["exit_description"]
                loc = world.get_location(loc_id)
                if loc and exit_desc in loc.exits:
                    del loc.exits[exit_desc]
                    logging.info(f"Removed exit '{exit_desc}' from location '{loc_id}'.")

        except (KeyError, TypeError) as e:
            logging.error(f"Invalid world mutation format for op '{op}'. Error: {e}. Mutation: {mutation}")

def execute_npc_schedules(game_state: GameState, world: GameWorld):
    current_hour = (game_state.minutes_elapsed // 60) % 24
    
    mutations_to_execute = []

    for location in world.locations.values():
        for character in location.characters:
            if not character.schedule:
                continue
            
            target_location_id = character.schedule.get(f"{current_hour:02d}:00")
            if target_location_id and location.id != target_location_id:
                mutation = {
                    "op": "move_npc",
                    "character_name": character.name,
                    "new_location_id": target_location_id
                }
                mutations_to_execute.append(mutation)
                logging.info(f"NPC '{character.name}' is scheduled to move to '{target_location_id}'.")

    if mutations_to_execute:
        execute_world_mutations(game_state, world, mutations_to_execute)

def check_and_trigger_world_events(
    game_state: GameState,
    world: GameWorld,
    ai_manager: 'AIManager',
    old_minutes: int,
    display: DisplayManager,
    managers: Dict[str, Any]
):
    old_hour = old_minutes // 60
    new_hour = game_state.minutes_elapsed // 60
    
    if new_hour > old_hour:
        logging.info(f"Time has passed into a new hour ({old_hour} -> {new_hour}). Checking for world events.")
        
        execute_npc_schedules(game_state, world)

        npc_behavior_manager = managers.get("npc_behavior")
        if npc_behavior_manager:
            npc_mutations = npc_behavior_manager.update_behaviors(game_state, world, ai_manager)
            if npc_mutations:
                execute_world_mutations(game_state, world, npc_mutations)
        
        weather_manager = managers.get("weather")
        if weather_manager:
            weather_mutations = weather_manager.update_weather(game_state, world, ai_manager)
            if weather_mutations:
                execute_world_mutations(game_state, world, weather_mutations)
        
        event_data = ai_manager.generate_world_event(game_state, world)
        if event_data:
            summary = event_data.get("narration_summary")
            mutations = event_data.get("mutations", [])
            
            if summary:
                display.system_message(f"\n[Time Passes...] {summary}")
            
            if mutations:
                execute_world_mutations(game_state, world, mutations)

def handle_npc_state_update(game_state: GameState, world: GameWorld, ai_manager: 'AIManager', intent_data: Dict, action_desc: str, narration: str):
    if intent_data.get("intent") != "dialogue":
        return

    target_name = intent_data.get("target")
    if not target_name:
        return

    npc = game_state.find_character_in_location(target_name, world)
    if not npc:
        return

    npc_update_data = ai_manager.update_npc_state(npc, action_desc, narration)
    if npc_update_data:
        new_mood = npc_update_data.get("new_mood")
        new_memory = npc_update_data.get("new_memory")
        if new_mood:
            logging.info(f"Updating NPC '{npc.name}' mood from '{npc.mood}' to '{new_mood}'.")
            npc.mood = new_mood
        if new_memory:
            logging.info(f"Adding new memory to NPC '{npc.name}': '{new_memory}'")
            npc.memory.append(new_memory)