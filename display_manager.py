import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from definitions.entities import Character
    from definitions.world_objects import Location
    from game_state import GameState
    from game_mechanics import calculate_stat_modifier

class DisplayManager:
    def __init__(self, line_width: int = 80):
        self.line_width = line_width

    def _print_header(self, title: str):
        print(f"\n--- {title} ".ljust(self.line_width, "-"))

    def _print_footer(self):
        print("-" * self.line_width)

    def narrate(self, text: str):
        print(f"\n{text}")

    def system_message(self, text: str):
        print(text)

    def show_error(self, text: str):
        print(f"\n[ERROR] {text}")

    def show_location(self, location: Optional['Location']):
        if not location:
            logging.error("DisplayManager cannot print location: Location object is None.")
            self.narrate("You are utterly lost in a formless void.")
            return

        print(f"\nLocation: {location.name}")
        print(location.description)
        if location.items:
            print("You see:", ", ".join(item.name for item in location.items) + ".")
        if location.characters:
            print("People here:", ", ".join(char.name for char in location.characters) + ".")
        
        if location.exits:
            print("Exits:")
            for exit_desc in location.exits.keys():
                print(f" - {exit_desc.capitalize()}")

    def show_player_character(self, player: 'Character'):
        self.system_message(f"You are {player.name}, {player.description}")

    def show_inventory(self, player: 'Character'):
        self._print_header("Inventory")
        if not player.inventory:
            print("You are carrying nothing.")
        else:
            for item in player.inventory:
                print(f" - {item.name} (Value: {item.value})")
        print(f"Coin: {player.money} copper pieces")
        self._print_footer()

    def show_character_sheet(self, player: 'Character'):
        from game_mechanics import calculate_stat_modifier
        self._print_header("Character Sheet")
        print(f"Name: {player.name}")
        print(f"HP: {player.hp} / {player.max_hp}")
        print(f"Level: {player.level} ({player.xp}/{player.xp_to_next_level} XP)")
        print(f"Armor Class: {player.get_total_armor_class()}")
        print("\nAttributes:")
        for stat, value in player.stats.items():
            modifier = calculate_stat_modifier(value)
            print(f"  - {stat.capitalize():>12}: {value} ({modifier:+.0f})")
        self._print_footer()

    def show_equipment(self, player: 'Character'):
        self._print_header("Equipped Items")
        equipped_any = False
        all_slots = ["main_hand", "off_hand", "head", "chest", "legs", "feet", "hands", "amulet", "ring"]
        for slot in all_slots:
            item = player.equipment.get(slot)
            if item:
                print(f"  - {slot.replace('_', ' ').title():>9}: {item.name}")
                equipped_any = True
        
        if not equipped_any:
            print("You have nothing equipped.")
        self._print_footer()
        
    def show_quest_journal(self, game_state: 'GameState'):
        self._print_header("Quest Journal")
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
        self._print_footer()

    def show_help(self):
        self._print_header("Help Menu")
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
        self._print_footer()

    def show_level_up(self, player: 'Character'):
        self.narrate(f"[Congratulations! You have reached Level {player.level}!]")
        print(f"  Max HP increased to {player.max_hp}.")
        print(f"  All your stats have increased by 1.")
        print(f"  You feel stronger.")

    def show_reputation_change(self, faction: str, change: int):
        direction = "increased" if change > 0 else "decreased"
        self.system_message(f"[Your reputation with {faction.replace('_', ' ').title()} has {direction}.]")

    def show_quest_started(self, quest_name: str, quest_description: str):
        self.narrate(f"[New Quest Started: {quest_name}]")
        print(f"  {quest_description}")
        
    def show_objective_complete(self, objective_description: str):
        self.narrate(f"[Objective Complete: {objective_description}]")

    def show_quest_complete(self, quest_name: str):
        self.narrate(f"[Quest Complete: {quest_name}]")