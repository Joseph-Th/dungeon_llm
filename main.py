import logging

from ai_manager import AIManager
from game_state import GameState, Character, Location, Item
from game_mechanics import perform_skill_check
from persistence import PersistenceManager

def setup_new_game() -> GameState:
    logging.info("Setting up a new game world.")
    player = Character(
        name="Arion",
        description="A determined adventurer with a strong arm and a quick wit.",
        stats={"strength": 16, "dexterity": 12, "intelligence": 14},
        inventory=[Item(name="worn leather satchel", description="Carries your meager belongings.")]
    )
    bartender = Character(
        name="Grog",
        description="A burly, red-faced man with a permanent scowl. He's polishing a glass with a dirty rag.",
        stats={"strength": 15, "dexterity": 9, "intelligence": 8}
    )
    starting_location = Location(
        name="The Salty Siren Tavern",
        description="A dimly lit, smoky tavern. The air smells of stale ale and sawdust. An old, sturdy-looking oak door with an iron lock leads to the back room.",
        characters=[bartender],
        items=[Item(name="a mysterious amulet", description="A silver amulet that hums with a faint, unseen energy.")]
    )
    return GameState(player=player, current_location=starting_location)

def main():
    logging.info("--- Gemini Dungeon Master Initializing ---")
    persistence_manager = PersistenceManager()

    print("\n--- Welcome to Gemini Dungeon Master ---")
    
    game_state = None
    existing_saves = persistence_manager.list_save_games()
    if existing_saves:
        print("Found existing save games:", ", ".join(existing_saves))
        choice = input("Type a save name to load, or type 'new' to start a new game: ").lower()
        if choice in existing_saves:
            game_state = persistence_manager.load_game(choice)
        elif choice != 'new':
            print(f"Save '{choice}' not found. Starting a new game.")

    if not game_state:
        game_state = setup_new_game()

    try:
        ai_manager = AIManager()
    except Exception as e:
        logging.critical(f"Failed to initialize the AI Manager. Exiting. Error: {e}")
        return

    print("\n--- Your Adventure Begins ---")
    print(f"You are {game_state.player.name}, {game_state.player.description}")
    print(f"\nLocation: {game_state.current_location.name}")
    print(game_state.current_location.description)

    while True:
        try:
            full_input = input("\n> ")
            if not full_input:
                continue
            
            command_parts = full_input.lower().split()
            command = command_parts[0]

            if command in ["quit", "exit"]:
                print("Thank you for playing!")
                break
            
            elif command == "save":
                if len(command_parts) > 1:
                    slot_name = command_parts[1]
                    if persistence_manager.save_game(game_state, slot_name):
                        print(f"Game saved to slot '{slot_name}'.")
                    else:
                        print("Failed to save the game.")
                else:
                    print("Usage: save <slot_name>")
                continue
            
            elif command == "load":
                if len(command_parts) > 1:
                    slot_name = command_parts[1]
                    loaded_state = persistence_manager.load_game(slot_name)
                    if loaded_state:
                        game_state = loaded_state
                        print(f"Game loaded from slot '{slot_name}'.")
                        print(f"\nLocation: {game_state.current_location.name}")
                        print(game_state.current_location.description)
                    else:
                        print(f"Failed to load game from slot '{slot_name}'.")
                else:
                    print("Usage: load <slot_name>")
                continue

            # If not a system command, treat it as a player action for the AI
            game_state.turn_count += 1
            intent_data = ai_manager.get_player_intent(game_state, full_input)
            if not intent_data or "intent" not in intent_data:
                print("\nThe DM seems to have misunderstood you. Please try rephrasing your action.")
                continue

            intent = intent_data.get("intent")
            narration = "An unexpected silence fills the air. Nothing happens."

            if intent == "skill_check":
                action_desc = intent_data.get("action_description", "An unspecified action.")
                mechanics_data = ai_manager.determine_skill_check_details(game_state, action_desc)
                if not mechanics_data or "skill" not in mechanics_data or "dc" not in mechanics_data:
                    narration = "The DM seems confused about the rules for that. Let's try something else."
                else:
                    success = perform_skill_check(game_state.player, mechanics_data["skill"], mechanics_data["dc"])
                    narration = ai_manager.narrate_outcome(game_state, action_desc, "Success" if success else "Failure")
            elif intent in ["look", "dialogue", "other"]:
                action_desc = intent_data.get("action_description", f"The player attempts the following: {full_input}")
                narration = ai_manager.narrate_outcome(game_state, action_desc, "Automatic Success")
            else:
                logging.warning(f"AI returned an unknown intent: '{intent}'")
                narration = f"You attempt to '{intent}', but the world doesn't seem to understand what that means."

            print(f"\n{narration}")
            logging.warning("Game state has not been mutated by this action. This is a future implementation step.")

        except KeyboardInterrupt:
            print("\nExiting game. Goodbye!")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            print("\nA critical error occurred. The game must end. Please check the logs.")
            break

if __name__ == "__main__":
    main()