"""
Run a full AI-powered Werewolf game with AgentScope agents.

Prerequisites:
- pip install agentscope
- Edit werewolf/config.py to set your model backend and API keys

Usage (PowerShell):
  .\env\Scripts\Activate.ps1
  python run_game.py --game-type six --model dashscope_chat --rounds 10 --discuss 2

Tip: For local models via Ollama, ensure Ollama is running and set --model ollama_chat.
"""

from __future__ import annotations

import argparse
import sys

try:
    from agentscope import init as ags_init  # type: ignore
    import agentscope  # type: ignore
except Exception as e:  # pragma: no cover
    print(
        "ERROR: agentscope is not installed. Run: pip install agentscope",
        file=sys.stderr,
    )
    raise

from werewolf.config import (
    MODEL_CONFIGS,
    DEFAULT_MODEL,
    GAME_CONFIG,
    PLAYER_NAMES_6,
    PLAYER_NAMES_9,
    PLAYER_NAMES_12,
    get_available_model,
)
from werewolf.orchestrator import WerewolfGameOrchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Werewolf multi-agent game")
    parser.add_argument(
        "--game-type",
        choices=["six", "nine", "twelve"],
        default=GAME_CONFIG.get("game_type", "nine"),
        help="Preset role distribution",
    )
    parser.add_argument(
        "--model",
        default=None,  # Will auto-detect if not specified
        help="Model config name (auto-detected if not specified)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=GAME_CONFIG.get("max_rounds", 20),
        help="Max day/night rounds",
    )
    parser.add_argument(
        "--discuss",
        type=int,
        default=GAME_CONFIG.get("discussion_rounds", 3),
        help="Discussion rounds per day",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=GAME_CONFIG.get("verbose", True),
        help="Print progress logs",
    )
    parser.add_argument(
        "--players",
        type=str,
        default="",
        help="Comma-separated custom player names (overrides presets)",
    )
    return parser.parse_args()


def pick_players(game_type: str, custom: list[str] | None) -> list[str]:
    if custom:
        return custom
    if game_type == "six":
        return PLAYER_NAMES_6
    if game_type == "nine":
        return PLAYER_NAMES_9
    return PLAYER_NAMES_12


def main():
    args = parse_args()

    # Auto-detect available model if not specified
    model_to_use = args.model if args.model else get_available_model()

    print(f"Starting Werewolf game with model: {model_to_use}")
    if not args.model:
        print(f"   (Auto-detected from available API keys)")

    # Initialize AgentScope with model configurations
    # Import the models module to register configurations
    try:
        import agentscope.models

        # Register all model configurations
        agentscope.models.clear_model_configs()
        for config in MODEL_CONFIGS:
            agentscope.models.read_model_configs(config)
    except (AttributeError, ImportError):
        # Older AgentScope version - configs passed differently
        pass

    ags_init(project="werewolf_game", name=f"game_{args.game_type}")

    players = pick_players(
        args.game_type,
        [p.strip() for p in args.players.split(",") if p.strip()] or None,
    )

    orchestrator = WerewolfGameOrchestrator(
        player_names=players,
        model_config_name=model_to_use,
        game_type=args.game_type,
        max_rounds=args.rounds,
        verbose=args.verbose,
    )

    winner = orchestrator.run_game()

    summary = orchestrator.get_game_summary()
    print("\n=== Game Summary ===")
    print(f"Winner: {summary['winner']}")
    print(f"Rounds: {summary['rounds']}")
    print("Roles:")
    for p, r in summary["roles"].items():
        status = "ALIVE" if p in summary["survivors"] else "DEAD"
        print(f"  - {p}: {r} ({status})")

    # Log file was written in real-time during the game
    print(f"\nComplete game transcript saved to: {orchestrator.log_file}")


if __name__ == "__main__":
    main()
