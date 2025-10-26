import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


class Role(Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"
    GUARDIAN = "guardian"


class GamePhase(Enum):
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"


@dataclass
class GameState:


class WerewolfGame:
    def __init__