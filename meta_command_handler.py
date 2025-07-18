import logging
from typing import List, Optional, Tuple

from game_state import GameState, GameWorld, Character, Item
from persistence import PersistenceManager
from game_mechanics import calculate_stat_modifier
from display_manager import DisplayManager

class MetaCommandHandler:
    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence_manager = persistence_manager
        
        self.no_arg_commands = {"quit", "exit", "inventory", "i", "stats", "character", "quests", "journal", "equipment", "eq", "help"}
        self.arg_commands = {"save", "load"}
        self.all_commands = self.no_arg_commands.union(self.arg_commands)

    def handle_command(self, full_input: str, game_state: GameState, world: GameWorld, display: DisplayManager) -> Tuple[bool, Optional[GameState], Optional[GameWorld]]:
        command_parts = full_input.lower().split()
        command = command_parts[0]

        if command not in self.all_commands:
            return False, game_state, world

        if command in self.no_arg_commands and len(command_parts) > 1:
            return False, game_state, world
        
        if command in self.arg_commands and len(command_parts) == 1:
            display.system_message(f"Usage: {command} <name>")
            return True, game_state, world

        if command in ["quit", "exit"]:
            self._handle_quit(display)
            return True, None, None

        elif command == "save":
            self._handle_save(command_parts, game_state, world, display)
            return True, game_state, world

        elif command == "load":
            loaded_data = self._handle_load(command_parts, display)
            if loaded_data:
                game_state, world = loaded_data
                display.system_message(f"Game loaded from slot '{command_parts[1]}'.")
                display.show_location(game_state.get_current_location(world))
                return True, game_state, world
            return True, game_state, world

        elif command in ["inventory", "i"]:
            display.show_inventory(game_state.player)
            return True, game_state, world
        
        elif command in ["stats", "character"]:
            display.show_character_sheet(game_state.player)
            return True, game_state, world
        
        elif command in ["quests", "journal"]:
            display.show_quest_journal(game_state)
            return True, game_state, world

        elif command in ["equipment", "eq"]:
            display.show_equipment(game_state.player)
            return True, game_state, world

        elif command == "help":
            display.show_help()
            return True, game_state, world
        
        return False, game_state, world

    def _handle_quit(self, display: DisplayManager):
        display.system_message("Thank you for playing!")

    def _handle_save(self, command_parts: List[str], game_state: GameState, world: GameWorld, display: DisplayManager):
        if len(command_parts) > 1:
            slot_name = command_parts[1]
            if self.persistence_manager.save_game(game_state, world, slot_name):
                display.system_message(f"Game saved to slot '{slot_name}'.")
            else:
                display.show_error("Failed to save the game.")
        else:
            display.system_message("Usage: save <slot_name>")
            
    def _handle_load(self, command_parts: List[str], display: DisplayManager) -> Optional[Tuple[GameState, GameWorld]]:
        if len(command_parts) > 1:
            slot_name = command_parts[1]
            loaded_data = self.persistence_manager.load_game(slot_name)
            if loaded_data:
                return loaded_data
            else:
                display.show_error(f"Failed to load game from slot '{slot_name}'.")
        else:
            display.system_message("Usage: load <slot_name>")
        return None