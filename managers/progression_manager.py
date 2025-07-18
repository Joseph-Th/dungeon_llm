import logging
from typing import Dict, Any

from definitions.entities import Character
from game_state import GameState
from display_manager import DisplayManager

class ProgressionManager:

    def award_xp(self, game_state: GameState, amount: int, display: DisplayManager):
        if amount <= 0:
            return

        player = game_state.player
        player.xp += amount
        logging.info(f"Player awarded {amount} XP. Total XP: {player.xp}")
        display.system_message(f"\n[You gained {amount} experience points!]")

        self.check_for_levelup(game_state, display)

    def check_for_levelup(self, game_state: GameState, display: DisplayManager):
        player = game_state.player
        
        leveled_up = False
        while player.xp >= player.xp_to_next_level:
            leveled_up = True
            
            player.xp -= player.xp_to_next_level
            
            player.level += 1
            
            player.xp_to_next_level = int(player.xp_to_next_level * 1.5)
            
            logging.info(f"Player leveled up to Level {player.level}!")
            self._apply_level_up_bonuses(player)
        
        if leveled_up:
            display.show_level_up(player)

    def _apply_level_up_bonuses(self, player: Character):
        player.max_hp += 5
        player.hp = player.max_hp
        
        for stat in player.stats:
            player.stats[stat] += 1