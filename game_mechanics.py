import random
import logging
from typing import Dict

from game_state import Character

def calculate_stat_modifier(stat_value: int) -> int:
    return (stat_value - 10) // 2

def perform_skill_check(player: Character, skill: str, dc: int) -> bool:
    skill = skill.lower()
    player_stat_value = player.stats.get(skill, 10)
    
    if player_stat_value is None:
        logging.warning(f"Player '{player.name}' has no stat named '{skill}'. Defaulting to 10.")
        player_stat_value = 10
        
    modifier = calculate_stat_modifier(player_stat_value)
    roll = random.randint(1, 20)
    total = roll + modifier

    logging.info(f"--- SKILL CHECK: {skill.upper()} ---")
    logging.info(f"  - Difficulty Class (DC): {dc}")
    logging.info(f"  - Player Stat ({skill}): {player_stat_value} (Modifier: {modifier:+.0f})")
    logging.info(f"  - Dice Roll (d20): {roll}")
    logging.info(f"  - Total: {total}")

    if total >= dc:
        logging.info("  - Result: SUCCESS")
        return True
    else:
        logging.info("  - Result: FAILURE")
        return False