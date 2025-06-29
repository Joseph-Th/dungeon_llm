import logging
from typing import Tuple, Optional, Dict, Any

from ai_manager import AIManager
from game_state import GameState, GameWorld
from definitions.entities import Character, Item
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
from quest_manager import QuestManager
from progression_manager import ProgressionManager
from reputation_manager import ReputationManager

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

def print_location(game_state: GameState, world: GameWorld):
    current_location = game_state.get_current_location(world)
    if not current_location:
        logging.error(f"Cannot print location: Player's location ID '{game_state.current_location_id}' is invalid.")
        print("\nYou are utterly lost in a formless void.")
        return
    
    print(f"\nLocation: {current_location.name}")
    print(current_location.description)
    if current_location.items:
        print("You see:", ", ".join(item.name for item in current_location.items) + ".")
    if current_location.characters:
        print("People here:", ", ".join(char.name for char in current_location.characters) + ".")
    
    if current_location.exits:
        print("Exits:")
        for exit_desc in current_location.exits.keys():
            print(f" - {exit_desc.capitalize()}")

def game_loop(
    game_state: GameState, 
    world: GameWorld, 
    ai_manager: AIManager, 
    meta_handler: MetaCommandHandler,
    intent_handlers: Dict[str, Any],
    reputation_manager: ReputationManager
):
    quest_manager = intent_handlers["quest_manager"]
    progression_manager = intent_handlers["progression_manager"]
    command_aliases = { "i": "inventory", "eq": "equipment", "l": "look" }

    while True:
        try:
            prompt_str = "> "
            if game_state.combat_state:
                # Check if it's the player's turn before changing prompt
                if len(game_state.combat_state["participants"]) > game_state.combat_state["turn_index"]:
                    active_char_name = game_state.combat_state["participants"][game_state.combat_state["turn_index"]]
                    if active_char_name == game_state.player.name:
                        prompt_str = "[COMBAT] > "

            full_input = input(f"\n{prompt_str}")
            if not full_input:
                continue
            
            # --- ALIAS LOGIC FIX ---
            # Check if the entire stripped input is an alias, not just the first word.
            processed_input = full_input.lower().strip()
            if processed_input in command_aliases:
                full_input = command_aliases[processed_input]
            
            command_was_handled, new_state, new_world = meta_handler.handle_command(full_input, game_state, world)
            
            if command_was_handled:
                if new_state is None: # Quit command was issued
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
                print("\nThe DM seems to have misunderstood you. Please try rephrasing your action.")
                continue

            intent = intent_data.get("intent")
            if not isinstance(intent, str):
                print("\nThe DM's intentions are unclear. Please try rephrasing your action.")
                continue

            action_desc = intent_data.get("action_description", f"The player attempts: {full_input}")
            result_string = f"Failure: The intent '{intent}' is not recognized by the game."

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
            print(f"\n{narration}")
            
            handle_npc_state_update(game_state, world, ai_manager, intent_data, action_desc, narration)

            if intent == "give_item" or intent == "attack":
                target_name = intent_data.get("target")
                target_char = game_state.find_character_in_location(target_name, world) if target_name else None
                reputation_manager.process_event(game_state, intent, target_char)

            if intent == "move" and "Success" in result_string and game_state.current_location_id != original_location_id:
                print_location(game_state, world)
            
            if intent == "look" and intent_data.get("target") is None:
                print_location(game_state, world)

            quest_manager.check_for_updates(game_state, intent, result_string, intent_data)
            progression_manager.check_for_levelup(game_state)
            check_and_trigger_world_events(game_state, world, ai_manager, old_minutes_elapsed)

        except KeyboardInterrupt:
            print("\nExiting game. Goodbye!")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            print("\nA critical error occurred. The game must end. Please check the logs.")
            break

def main():
    logging.info("--- Gemini Dungeon Master Initializing ---")
    
    persistence_manager = PersistenceManager()
    action_processor = ActionProcessor()
    meta_handler = MetaCommandHandler(persistence_manager)
    item_handler = ItemHandler()
    combat_handler = CombatHandler()
    interaction_handler = InteractionHandler()
    dialogue_handler = DialogueHandler()
    equipment_handler = EquipmentHandler()
    quest_manager = QuestManager()
    progression_manager = ProgressionManager()
    reputation_manager = ReputationManager()

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
        "quest_manager": quest_manager,
        "progression_manager": progression_manager
    }

    print("\n--- Welcome to Gemini Dungeon Master ---")
    
    game_state: Optional[GameState] = None
    world: Optional[GameWorld] = None
    
    existing_saves = persistence_manager.list_save_games()
    if existing_saves:
        print("Found existing save games:", ", ".join(existing_saves))
        choice = input("Type a save name to load, or type 'new' to start a new game: ").lower()
        if choice != 'new':
            loaded_data = persistence_manager.load_game(choice)
            if loaded_data:
                game_state, world = loaded_data

    if not game_state or not world:
        try:
            game_state, world = setup_new_game()
            print("\n--- Your Adventure Begins ---")
        except Exception as e:
            logging.critical(f"Failed to setup new game from world data. Error: {e}")
            print("\nFATAL ERROR: Could not load the game world. Please check game data files.")
            return
    else:
        print("\n--- Resuming Your Adventure ---")

    if not game_state or not world:
        logging.critical("FATAL: Game state or world could not be initialized.")
        print("\nA critical error prevented the game from starting. Please check logs.")
        return

    try:
        ai_manager = AIManager()
    except Exception as e:
        logging.critical(f"Failed to initialize the AI Manager. Exiting. Error: {e}")
        return

    print(f"You are {game_state.player.name}, {game_state.player.description}")
    print_location(game_state, world)

    game_loop(game_state, world, ai_manager, meta_handler, intent_handlers, reputation_manager)

if __name__ == "__main__":
    main()