import logging
from typing import Dict, Any, Optional

from game_state import GameState, Character
from display_manager import DisplayManager

class ReputationManager:
    
    def __init__(self):
        logging.info("ReputationManager initialized.")
        self.reputation_map = {
            "town_guard": {
                "give_item": 5,
                "attack": -50,
            },
            "thieves_guild": {
                "attack": -20,
                "give_item": 2,
            }
        }

    def process_event(self, game_state: GameState, intent: str, display: DisplayManager, target: Optional[Character] = None):
        if not target or not target.faction:
            return

        faction = target.faction
        intent_effects = self.reputation_map.get(faction)

        if not intent_effects:
            return

        reputation_change = intent_effects.get(intent, 0)

        if reputation_change != 0:
            self._adjust_reputation(game_state, faction, reputation_change, display)

    def _adjust_reputation(self, game_state: GameState, faction: str, amount: int, display: DisplayManager):
        if faction not in game_state.reputation:
            game_state.reputation[faction] = 0
        
        game_state.reputation[faction] += amount
        
        logging.info(f"Reputation with '{faction}' changed by {amount}. New reputation: {game_state.reputation[faction]}.")
        display.show_reputation_change(faction, amount)
            
    def get_reputation_level(self, game_state: GameState, faction: str) -> str:
        score = game_state.reputation.get(faction, 0)
        
        if score > 50:
            return "revered"
        elif score > 20:
            return "trusted"
        elif score > 5:
            return "friendly"
        elif score < -50:
            return "hated"
        elif score < -20:
            return "disliked"
        elif score < -5:
            return "unfriendly"
        else:
            return "neutral"