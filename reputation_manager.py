import logging
from typing import Dict, Any, Optional

from game_state import GameState, Character

class ReputationManager:
    
    def __init__(self):
        logging.info("ReputationManager initialized.")
        # Define how much reputation changes for specific actions.
        # This can be expanded with more intents and factions.
        self.reputation_map = {
            "town_guard": {
                "give_item": 5,
                "attack": -50,
            },
            "thieves_guild": {
                "attack": -20,
                "give_item": 2, # They might be suspicious
            }
        }

    def process_event(self, game_state: GameState, intent: str, target: Optional[Character] = None):
        """
        Updates player's reputation based on an action taken.
        """
        if not target or not target.faction:
            return

        faction = target.faction
        intent_effects = self.reputation_map.get(faction)

        if not intent_effects:
            return

        reputation_change = intent_effects.get(intent, 0)

        if reputation_change != 0:
            self._adjust_reputation(game_state, faction, reputation_change)

    def _adjust_reputation(self, game_state: GameState, faction: str, amount: int):
        """
        Safely adjusts the reputation for a given faction.
        """
        if faction not in game_state.reputation:
            game_state.reputation[faction] = 0
        
        game_state.reputation[faction] += amount
        
        logging.info(f"Reputation with '{faction}' changed by {amount}. New reputation: {game_state.reputation[faction]}.")
        if amount > 0:
            print(f"[Your reputation with {faction.replace('_', ' ').title()} has increased.]")
        else:
            print(f"[Your reputation with {faction.replace('_', ' ').title()} has decreased.]")
            
    def get_reputation_level(self, game_state: GameState, faction: str) -> str:
        """
        Translates a numerical reputation score into a descriptive level.
        """
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