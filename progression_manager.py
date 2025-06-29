import logging
from typing import Dict, Any

from definitions.entities import Character
from game_state import GameState

class ProgressionManager:

    def award_xp(self, game_state: GameState, amount: int):
        if amount <= 0:
            return

        player = game_state.player
        player.xp += amount
        logging.info(f"Player awarded {amount} XP. Total XP: {player.xp}")
        print(f"\n[You gained {amount} experience points!]")

        self.check_for_levelup(game_state)

    def check_for_levelup(self, game_state: GameState):
        player = game_state.player
        
        leveled_up = False
        while player.xp >= player.xp_to_next_level:
            leveled_up = True
            
            # Carry over excess XP
            player.xp -= player.xp_to_next_level
            
            player.level += 1
            
            # Increase XP requirement for the next level (e.g., 50% more)
            player.xp_to_next_level = int(player.xp_to_next_level * 1.5)
            
            logging.info(f"Player leveled up to Level {player.level}!")
            self._apply_level_up_bonuses(player)
        
        if leveled_up:
            print(f"\n[Congratulations! You have reached Level {player.level}!]")
            print(f"  Max HP increased to {player.max_hp}.")
            print(f"  All your stats have increased by 1.")
            print(f"  You feel stronger.")

    def _apply_level_up_bonuses(self, player: Character):
        # Simple level up: +1 to all stats and +5 to max HP
        
        player.max_hp += 5
        player.hp = player.max_hp # Full heal on level up
        
        for stat in player.stats:
            player.stats[stat] += 1
            
        # A more complex system could offer choices:
        # e.g., "Choose one stat to increase by 2"
        # This would require prompting the user for input here.