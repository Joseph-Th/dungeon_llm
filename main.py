import logging
from typing import Tuple, Optional, Dict, Any

from ai_manager import AIManager
from game_state import GameState, GameWorld
from definitions.entities import Character
from game_mechanics import perform_skill_check
from persistence import PersistenceManager
from action_processor import ActionProcessor
from meta_command_handler import MetaCommandHandler
from world_loader import WorldLoader
from event_executor import (
    execute_player_mutations, 
    check_and_trigger_world_events,
    handle_npc_state_update
)
from action_handlers.item_handler import ItemHandler
from action_handlers.combat_handler import CombatHandler
from action_handlers.interaction_handler import InteractionHandler
from action_handlers.dialogue_handler import DialogueHandler
from action_handlers.equipment_handler import EquipmentHandler
from action_handlers.crafting_handler import CraftingHandler
from action_handlers.quest_handler import QuestHandler
from display_manager import DisplayManager

# Corrected imports from the new managers/ directory
from managers.quest_manager import QuestManager
from managers.progression_manager import ProgressionManager
from managers.reputation_manager import ReputationManager
from managers.companion_manager import CompanionManager
from managers.npc_behavior_manager import NPCBehaviorManager
from managers.weather_manager import WeatherManager

def setup_new_game() -> Tuple[GameState, GameWorld]:
    logging.info("Setting up a new game world.")
    
    world_loader = WorldLoader(locations_data_dir="data/locations")
    world = world_loader.load_world()

    player = Character(
        name="Arion",
        description="A determined adventurer with a strong arm and a quick wit.",
        stats={"strength": 16, "dexterity": 12, "intelligence": 14},
    )
    
    game_state = GameState(player=player, current_location_id="salty_siren_tavern")

    return game_state, world

def game_loop(
    game_state: GameState, 
    world: GameWorld, 
    ai_manager: AIManager, 
    meta_handler: MetaCommandHandler,
    intent_handlers: Dict[str, Any],
    display: DisplayManager,
    managers: Dict[str, Any]
):
    # Retrieve managers from the dictionary
    quest_manager = managers["quest"]
    progression_manager = managers["progression"]
    reputation_manager = managers["reputation"]
    
    command_aliases = { "i": "inventory", "eq": "equipment", "l": "look" }

    while True:
        try:
            prompt_str = "> "
            if game_state.combat_state:
                if len(game_state.combat_state["participants"]) > game_state.combat_state["turn_index"]:
                    active_char_name = game_state.combat_state["participants"][game_state.combat_state["turn_index"]]
                    if active_char_name == game_state.player.name:
                        prompt_str = "[COMBAT] > "

            full_input = input(f"\n{prompt_str}")
            if not full_input:
                continue
            
            processed_input = full_input.lower().strip()
            if processed_input in command_aliases:
                full_input = command_aliases[processed_input]
            
            command_was_handled, new_state, new_world = meta_handler.handle_command(full_input, game_state, world, display)
            
            if command_was_handled:
                if new_state is None:
                    break
                assert new_world is not None
                game_state = new_state
                world = new_world
                continue

            old_minutes_elapsed = game_state.minutes_elapsed
            game_state.turn_count += 1
            original_location_id = game_state.current_location_id
            
            intent_data = ai_manager.get_player_intent(game_state, world, full_input)
            if not intent_data or not isinstance(intent_data, dict):
                display.show_error("The DM seems to have misunderstood you. Please try rephrasing your action.")
                continue

            intent = intent_data.get("intent")
            if not isinstance(intent, str):
                display.show_error("The DM's intentions are unclear. Please try rephrasing your action.")
                continue

            action_desc = intent_data.get("action_description", f"The player attempts: {full_input}")
            result_string = f"Failure: The intent '{intent}' is not recognized by the game."

            # Pass the display manager to the handlers
            intent_data["display"] = display 

            handler = intent_handlers.get(intent)
            if handler:
                result_string = handler(game_state, world, ai_manager, intent_data)
            elif intent == "skill_check":
                mechanics_data = ai_manager.determine_skill_check_details(game_state, world, action_desc)
                if not mechanics_data or not mechanics_data.get("is_possible", False) or "skill" not in mechanics_data or "dc" not in mechanics_data:
                    result_string = "Failure: The DM seems confused about the rules for that."
                else:
                    success = perform_skill_check(game_state.player, mechanics_data["skill"], mechanics_data["dc"])
                    result_string = "Success" if success else "Failure"
                    mutations_to_apply = mechanics_data.get("on_success" if success else "on_failure", [])
                    execute_player_mutations(game_state, mutations_to_apply)

            if "Failure" not in result_string and "Impossible" not in result_string and not game_state.combat_state:
                 if intent != "pass_time":
                    game_state.minutes_elapsed += 5

            narration = ai_manager.narrate_outcome(game_state, world, action_desc, result_string)
            display.narrate(narration)
            
            handle_npc_state_update(game_state, world, ai_manager, intent_data, action_desc, narration)

            if intent == "give_item" or intent == "attack":
                target_name = intent_data.get("target")
                target_char = game_state.find_character_in_location(target_name, world) if target_name else None
                reputation_manager.process_event(game_state, intent, display, target=target_char)

            if intent == "move" and "Success" in result_string and game_state.current_location_id != original_location_id:
                display.show_location(game_state.get_current_location(world))
            
            if intent == "look" and intent_data.get("target") is None:
                display.show_location(game_state.get_current_location(world))

            quest_manager.check_for_updates(game_state, intent, result_string, intent_data, display)
            progression_manager.check_for_levelup(game_state, display)
            check_and_trigger_world_events(game_state, world, ai_manager, old_minutes_elapsed, display, managers)

        except KeyboardInterrupt:
            display.system_message("\nExiting game. Goodbye!")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            display.system_message("\nA critical error occurred. The game must end. Please check the logs.")
            break

def main():
    logging.info("--- Gemini Dungeon Master Initializing ---")
    
    # Core Components
    persistence_manager = PersistenceManager()
    action_processor = ActionProcessor()
    display = DisplayManager()
    meta_handler = MetaCommandHandler(persistence_manager)

    # Initialize Managers
    managers = {
        "quest": QuestManager(),
        "progression": ProgressionManager(),
        "reputation": ReputationManager(),
        "companion": CompanionManager(),
        "npc_behavior": NPCBehaviorManager(),
        "weather": WeatherManager()
    }

    # Initialize Handlers that depend on Managers
    quest_handler = QuestHandler(managers["quest"])
    
    # Initialize standalone Handlers
    item_handler = ItemHandler()
    combat_handler = CombatHandler()
    interaction_handler = InteractionHandler()
    dialogue_handler = DialogueHandler()
    equipment_handler = EquipmentHandler()
    crafting_handler = CraftingHandler()
    
    # Define all intent handlers
    intent_handlers: Dict[str, Any] = {
        "move": action_processor.process_action,
        "take_item": action_processor.process_action,
        "pass_time": action_processor.process_action,
        "use_item": item_handler.process_item_intent,
        "drop_item": item_handler.process_item_intent,
        "give_item": item_handler.process_item_intent,
        "attack": combat_handler.process_combat_intent,
        "interact": interaction_handler.process_interaction_intent,
        "look": interaction_handler.process_interaction_intent,
        "dialogue": dialogue_handler.process_dialogue_intent,
        "equip": equipment_handler.process_equipment_intent,
        "unequip": equipment_handler.process_equipment_intent,
        "craft_item": crafting_handler.process_crafting_intent,
        "quest_action": quest_handler.process_quest_intent,
        "companion_command": managers["companion"].process_command_intent,
    }

    display.system_message("\n--- Welcome to Gemini Dungeon Master ---")
    
    game_state: Optional[GameState] = None
    world: Optional[GameWorld] = None
    
    existing_saves = persistence_manager.list_save_games()
    if existing_saves:
        display.system_message(f"Found existing save games: {', '.join(existing_saves)}")
        choice = input("Type a save name to load, or type 'new' to start a new game: ").lower()
        if choice != 'new':
            loaded_data = persistence_manager.load_game(choice)
            if loaded_data:
                game_state, world = loaded_data

    if not game_state or not world:
        try:
            game_state, world = setup_new_game()
            display.system_message("\n--- Your Adventure Begins ---")
        except Exception as e:
            logging.critical(f"Failed to setup new game from world data. Error: {e}")
            display.system_message("\nFATAL ERROR: Could not load the game world. Please check game data files.")
            return
    else:
        display.system_message("\n--- Resuming Your Adventure ---")

    if not game_state or not world:
        logging.critical("FATAL: Game state or world could not be initialized.")
        display.system_message("\nA critical error prevented the game from starting. Please check logs.")
        return

    try:
        ai_manager = AIManager()
    except Exception as e:
        logging.critical(f"Failed to initialize the AI Manager. Exiting. Error: {e}")
        return
    
    display.show_player_character(game_state.player)
    display.show_location(game_state.get_current_location(world))

    game_loop(game_state, world, ai_manager, meta_handler, intent_handlers, display, managers)

if __name__ == "__main__":
    main()