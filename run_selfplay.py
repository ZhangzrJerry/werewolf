"""
Self-play training script for Werewolf game
Runs multiple games to iteratively improve agent strategies through learning

Features:
- Resumable: can be interrupted and resumed from latest strategies
- Progress tracking: saves metadata about training progress
- Parallel execution: optional multi-process parallelization
- Strategy persistence: automatically loads/saves strategies between games
"""

import os
import sys
import json
import datetime
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werewolf.orchestrator import WerewolfGameOrchestrator
from werewolf.config import MODEL_CONFIGS


def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs(os.path.join(".training", "strategies"), exist_ok=True)
    os.makedirs(os.path.join(".training", "game_logs"), exist_ok=True)
    os.makedirs(os.path.join(".training", "reviews"), exist_ok=True)
    os.makedirs(os.path.join(".training", "progress"), exist_ok=True)


def load_training_progress() -> Dict[str, Any]:
    """Load training progress metadata"""
    progress_file = os.path.join(".training", "progress", "progress.json")
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "total_games": 0,
        "last_updated": None,
        "games_history": [],
    }


def save_training_progress(progress: Dict[str, Any]):
    """Save training progress metadata"""
    progress_file = os.path.join(".training", "progress", "progress.json")
    progress["last_updated"] = datetime.datetime.now().isoformat()
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def run_single_game(
    game_num: int,
    model_config_name: str,
    game_type: str = "six",
    player_names: Optional[list] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run a single game and return summary

    Args:
        game_num: Game number for logging
        model_config_name: Model configuration to use
        game_type: Game type (six, nine, twelve)
        player_names: List of player names (default: Alice, Bob, Charlie, David, Eve, Frank)
        verbose: Print game progress

    Returns:
        Game summary dict with winner, rounds, etc.
    """
    if player_names is None:
        if game_type == "six":
            player_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        elif game_type == "nine":
            player_names = [
                "Alice",
                "Bob",
                "Charlie",
                "David",
                "Eve",
                "Frank",
                "Grace",
                "Henry",
                "Ivy",
            ]
        else:  # twelve
            player_names = [
                "Alice",
                "Bob",
                "Charlie",
                "David",
                "Eve",
                "Frank",
                "Grace",
                "Henry",
                "Ivy",
                "Jack",
                "Kate",
                "Leo",
            ]

    try:
        # Create orchestrator (will auto-load strategies from .training/strategies/)
        orchestrator = WerewolfGameOrchestrator(
            player_names=player_names,
            model_config_name=model_config_name,
            game_type=game_type,
            max_rounds=20,
            verbose=verbose,
        )

        # Run game
        winner = orchestrator.run_game()
        summary = orchestrator.get_game_summary()

        return {
            "game_num": game_num,
            "winner": winner,
            "rounds": summary["rounds"],
            "log_file": orchestrator.log_file,
            "success": True,
        }

    except Exception as e:
        print(f"[ERROR] Game {game_num} failed: {e}")
        import traceback

        traceback.print_exc()
        return {
            "game_num": game_num,
            "winner": None,
            "rounds": 0,
            "log_file": None,
            "success": False,
            "error": str(e),
        }


def run_training(
    num_games: int,
    model_config_name: str,
    game_type: str = "six",
    parallel: int = 1,
    verbose: bool = False,
    resume: bool = True,
):
    """Run self-play training for multiple games

    Args:
        num_games: Number of games to run
        model_config_name: Model configuration to use
        game_type: Game type (six, nine, twelve)
        parallel: Number of parallel workers (1 = sequential)
        verbose: Print detailed game progress
        resume: Continue from previous training progress
    """
    ensure_directories()

    # Load progress
    progress = (
        load_training_progress()
        if resume
        else {
            "total_games": 0,
            "last_updated": None,
            "games_history": [],
        }
    )

    start_game = progress["total_games"]
    print(f"\n{'='*70}")
    print(f"WEREWOLF SELF-PLAY TRAINING")
    print(f"{'='*70}")
    print(f"Model: {model_config_name}")
    print(f"Game type: {game_type}")
    print(f"Total games to run: {num_games}")
    print(f"Starting from game: {start_game + 1}")
    print(f"Parallel workers: {parallel}")
    print(f"Resume mode: {resume}")
    print(f"{'='*70}\n")

    # Statistics
    stats = {
        "werewolf_wins": 0,
        "villager_wins": 0,
        "draws": 0,
        "errors": 0,
        "total_rounds": 0,
    }

    try:
        if parallel > 1:
            # Parallel execution
            print(f"Running {num_games} games in parallel with {parallel} workers...\n")

            with ProcessPoolExecutor(max_workers=parallel) as executor:
                # Submit all games
                futures = {
                    executor.submit(
                        run_single_game,
                        start_game + i + 1,
                        model_config_name,
                        game_type,
                        None,
                        verbose,
                    ): i
                    for i in range(num_games)
                }

                # Process as they complete
                for future in as_completed(futures):
                    result = future.result()
                    game_idx = futures[future]
                    current_game = start_game + game_idx + 1

                    if result["success"]:
                        winner = result["winner"]
                        rounds = result["rounds"]

                        # Update stats
                        if winner == "werewolves":
                            stats["werewolf_wins"] += 1
                        elif winner == "villagers":
                            stats["villager_wins"] += 1
                        else:
                            stats["draws"] += 1
                        stats["total_rounds"] += rounds

                        # Save to progress
                        progress["games_history"].append(
                            {
                                "game_num": current_game,
                                "winner": winner,
                                "rounds": rounds,
                                "log_file": result["log_file"],
                                "timestamp": datetime.datetime.now().isoformat(),
                            }
                        )

                        print(
                            f"[{current_game}/{start_game + num_games}] "
                            f"Winner: {winner:12s} | Rounds: {rounds:2d} | "
                            f"W:{stats['werewolf_wins']} V:{stats['villager_wins']} D:{stats['draws']}"
                        )
                    else:
                        stats["errors"] += 1
                        print(f"[{current_game}/{start_game + num_games}] FAILED")

                    # Update progress periodically
                    progress["total_games"] = current_game
                    if current_game % max(1, num_games // 10) == 0:
                        save_training_progress(progress)

        else:
            # Sequential execution
            print(f"Running {num_games} games sequentially...\n")

            for i in range(num_games):
                current_game = start_game + i + 1
                print(f"\n[Game {current_game}/{start_game + num_games}]")

                result = run_single_game(
                    current_game, model_config_name, game_type, None, verbose
                )

                if result["success"]:
                    winner = result["winner"]
                    rounds = result["rounds"]

                    # Update stats
                    if winner == "werewolves":
                        stats["werewolf_wins"] += 1
                    elif winner == "villagers":
                        stats["villager_wins"] += 1
                    else:
                        stats["draws"] += 1
                    stats["total_rounds"] += rounds

                    # Save to progress
                    progress["games_history"].append(
                        {
                            "game_num": current_game,
                            "winner": winner,
                            "rounds": rounds,
                            "log_file": result["log_file"],
                            "timestamp": datetime.datetime.now().isoformat(),
                        }
                    )

                    print(
                        f"Winner: {winner} | Rounds: {rounds} | "
                        f"Cumulative - W:{stats['werewolf_wins']} V:{stats['villager_wins']} D:{stats['draws']}"
                    )
                else:
                    stats["errors"] += 1

                # Update progress after each game
                progress["total_games"] = current_game
                save_training_progress(progress)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Training interrupted by user")
        print("Progress has been saved. You can resume by running this script again.")
        save_training_progress(progress)

    # Final summary
    print(f"\n{'='*70}")
    print(f"TRAINING SUMMARY")
    print(f"{'='*70}")
    print(f"Total games completed: {progress['total_games']}")
    print(f"Werewolf wins: {stats['werewolf_wins']}")
    print(f"Villager wins: {stats['villager_wins']}")
    print(f"Draws: {stats['draws']}")
    print(f"Errors: {stats['errors']}")
    if stats["werewolf_wins"] + stats["villager_wins"] > 0:
        print(
            f"Average rounds per game: {stats['total_rounds'] / (stats['werewolf_wins'] + stats['villager_wins'] + stats['draws']):.2f}"
        )
    print(f"\nProgress saved to: .training/progress/progress.json")
    print(f"Strategies saved to: .training/strategies/")
    print(f"Game logs saved to: .training/game_logs/")
    print(f"Reviews saved to: .training/reviews/")
    print(f"{'='*70}\n")

    # Save final progress
    save_training_progress(progress)


def detect_model_config():
    """Auto-detect available model configuration"""
    for config in MODEL_CONFIGS:
        config_name = config.get("config_name", "")
        model_type = config.get("model_type", "")

        # Check if API key is available
        api_key = config.get("api_key")
        if api_key and len(api_key) > 10:  # Basic check that key exists
            print(f"Auto-detected model: {config_name} ({model_type})")
            return config_name

    print("Warning: No valid model configuration found with API key")
    return MODEL_CONFIGS[0]["config_name"] if MODEL_CONFIGS else None


def main():
    parser = argparse.ArgumentParser(
        description="Run self-play training for Werewolf game"
    )
    parser.add_argument(
        "-n",
        "--num-games",
        type=int,
        default=50,
        help="Number of games to run (default: 50)",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        help="Model configuration name (auto-detect if not specified)",
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        default="six",
        choices=["six", "nine", "twelve"],
        help="Game type (default: six)",
    )
    parser.add_argument(
        "-p",
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1, max: 8)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print detailed game progress"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh (ignore previous progress)",
    )

    args = parser.parse_args()

    # Detect model if not specified
    model_config_name = args.model or detect_model_config()
    if not model_config_name:
        print("Error: No model configuration available")
        return

    # Limit parallel workers
    parallel = max(1, min(8, args.parallel))

    # Run training
    run_training(
        num_games=args.num_games,
        model_config_name=model_config_name,
        game_type=args.type,
        parallel=parallel,
        verbose=args.verbose,
        resume=not args.no_resume,
    )


if __name__ == "__main__":
    main()
