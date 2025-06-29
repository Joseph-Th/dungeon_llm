import logging
from typing import List, Optional, Tuple

from game_state import GameState, GameWorld, Character, Item
from persistence import PersistenceManager
from game_mechanics import calculate_stat_modifier

class MetaCommandHandler:
    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence_manager = persistence_manager
        
        self.no_arg_commands = {"quit", "exit", "inventory", "i", "stats", "character", "quests", "journal", "equipment", "eq", "help"}
        self.arg_commands = {"save", "load"}
        self.all_commands = self.no_arg_commands.union(self.arg_commands)


    def handle_command(self, full_input: str, game_state: GameState, world: GameWorld) -> Tuple[bool, Optional[GameState], Optional[GameWorld]]:
        command_parts = full_input.lower().split()
        command = command_parts[0]

        if command not in self.all_commands:
            return False, game_state, world

        # --- NEW LOGIC TO PREVENT HIJACKING ---
        # If the command is a no-argument command, it must be the ONLY word.
        if command in self.no_arg_commands and len(command_parts) > 1:
            return False, game_state, world
        
        # If the command is an argument command, it must have an argument.
        if command in self.arg_commands and len(command_parts) == 1:
            print(f"Usage: {command} <name>")
            return True, game_state, world
        # --- END OF NEW LOGIC ---

        if command in ["quit", "exit"]:
            self._handle_quit()
            return True, None, None

        elif command == "save":
            self._handle_save(command_parts, game_state, world)
            return True, game_state, world

        elif command == "load":
            loaded_data = self._handle_load(command_parts)
            if loaded_data:
                return True, loaded_data[0], loaded_data[1]
            return True, game_state, world

        elif command in ["inventory", "i"]:
            self._handle_inventory(game_state.player)
            return True, game_state, world
        
        elif command in ["stats", "character"]:
            self._handle_stats(game_state.player)
            return True, game_state, world
        
        elif command in ["quests", "journal"]:
            self._handle_quests(game_state)
            return True, game_state, world

        elif command in ["equipment", "eq"]:
            self._handle_equipment(game_state.player)
            return True, game_state, world

        elif command == "help":
            self._handle_help()
            return True, game_state, world
        
        return False, game_state, world

    def _handle_quit(self):
        print("Thank you for playing!")

    def _handle_save(self, command_parts: List[str], game_state: GameState, world: GameWorld):
        if len(command_parts) > 1:
            slot_name = command_parts[1]
            if self.persistence_manager.save_game(game_state, world, slot_name):
                print(f"Game saved to slot '{slot_name}'.")
            else:
                print("Failed to save the game.")
        else:
            print("Usage: save <slot_name>")
            
    def _handle_load(self, command_parts: List[str]) -> Optional[Tuple[GameState, GameWorld]]:
        if len(command_parts) > 1:
            slot_name = command_parts[1]
            loaded_data = self.persistence_manager.load_game(slot_name)
            if loaded_data:
                game_state, world = loaded_data
                current_location = game_state.get_current_location(world)
                print(f"Game loaded from slot '{slot_name}'.")
                if current_location:
                    print(f"\nLocation: {current_location.name}")
                    print(current_location.description)
                return game_state, world
            else:
                print(f"Failed to load game from slot '{slot_name}'.")
        else:
            print("Usage: load <slot_name>")
        return None

    def _handle_inventory(self, player: Character):
        print("\n--- Inventory ---")
        if not player.inventory:
            print("You are carrying nothing.")
        else:
            for item in player.inventory:
                print(f" - {item.name} (Value: {item.value})")
        print(f"Coin: {player.money} copper pieces")
        print("-----------------")


    def _handle_stats(self, player: Character):
        print(f"\n--- Character Sheet ---")
        print(f"Name: {player.name}")
        print(f"HP: {player.hp} / {player.max_hp}")
        print(f"Level: {player.level} ({player.xp}/{player.xp_to_next_level} XP)")
        print(f"Armor Class: {player.get_total_armor_class()}")
        print("\nAttributes:")
        for stat, value in player.stats.items():
            modifier = calculate_stat_modifier(value)
            print(f"  - {stat.capitalize():>12}: {value} ({modifier:+.0f})")
        print("-----------------------")

    def _handle_equipment(self, player: Character):
        print("\n--- Equipped Items ---")
        equipped_any = False
        all_slots = ["main_hand", "off_hand", "head", "chest", "legs", "feet", "hands", "amulet", "ring"]
        for slot in all_slots:
            item = player.equipment.get(slot)
            if item:
                print(f"  - {slot.replace('_', ' ').title():>9}: {item.name}")
                equipped_any = True
        
        if not equipped_any:
            print("You have nothing equipped.")
        print("----------------------")
        
    def _handle_quests(self, game_state: GameState):
        print("\n--- Quest Journal ---")
        active_quests = [q for q in game_state.quest_log.values() if q.status == "active"]
        
        if not active_quests:
            print("You have no active quests.")
        else:
            for quest in active_quests:
                print(f"\n[ {quest.name} ]")
                print(f"  {quest.description}")
                for objective in quest.objectives:
                    status_marker = "[X]" if objective.is_complete else "[ ]"
                    print(f"    {status_marker} {objective.description}")
        print("--------------------")

    def _handle_help(self):
        print("\n--- Help Menu ---")
        print("This is a text adventure game where you type commands to interact with the world.")
        print("Try to phrase your actions naturally, for example: 'talk to the blacksmith' or 'attack the goblin with my sword'.")
        print("\nMeta-Commands (commands that are not part of the game world):")
        print("  - inventory (i)    : Show your inventory and money.")
        print("  - stats/character  : Display your character sheet.")
        print("  - equipment (eq)   : Show your currently equipped items.")
        print("  - quests/journal   : Display your active quests.")
        print("  - save <name>      : Save the game to a slot named <name>.")
        print("  - load <name>      : Load the game from slot <name>.")
        print("  - quit/exit        : Exit the game.")
        print("\nCommon in-game actions:")
        print("  - look / look at <thing>  : Observe your surroundings or something specific.")
        print("  - take <item>             : Pick up an item.")
        print("  - drop <item>             : Drop an item from your inventory.")
        print("  - equip <item>            : Equip an item from your inventory.")
        print("  - unequip <item>          : Unequip an item and return it to inventory.")
        print("  - talk to <person>        : Start a conversation.")
        print("  - attack <target>         : Initiate combat.")
        print("-----------------")