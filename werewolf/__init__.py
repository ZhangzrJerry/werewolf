"""
Werewolf Game Package
A multi-agent werewolf game implementation using AgentScope.
"""

from .werewolf_game import WerewolfGame, Role, GamePhase, GameState

# Export agent classes without forcing AgentScope at package import time
from .agents import (
    WerewolfAgentBase,
    VillagerAgent,
    WerewolfAgent,
    SeerAgent,
    WitchAgent,
    GuardianAgent,
    create_agent,
)

# Do NOT import orchestrator unconditionally to avoid requiring agentscope
# for consumers that only need core game logic. Users can import it directly
# via `from werewolf.orchestrator import WerewolfGameOrchestrator`.

__version__ = "0.1.0"
__all__ = [
    "WerewolfGame",
    "Role",
    "GamePhase",
    "GameState",
    "WerewolfAgentBase",
    "VillagerAgent",
    "WerewolfAgent",
    "SeerAgent",
    "WitchAgent",
    "GuardianAgent",
    "create_agent",
]
