from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import json
from pathlib import Path
from parser import GameLogParser
from state_manager import GameStateManager

app = Flask(__name__)

# Store current game state manager
current_game = None
game_data_cache = {}


def get_game_logs_directory():
    """Get the path to the game logs directory"""
    base_dir = Path(__file__).parent.parent
    logs_dir = base_dir / ".training" / "game_logs"
    return logs_dir


def get_available_logs():
    """Get list of available game log files (only completed games)"""
    logs_dir = get_game_logs_directory()

    if not logs_dir.exists():
        return []

    log_files = []
    for file_path in logs_dir.glob("*.txt"):
        # Quick check if game completed normally by looking for GAME OVER marker
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if (
                    "============================================================\nGAME OVER\n============================================================"
                    in content
                ):
                    log_files.append(
                        {
                            "filename": file_path.name,
                            "path": str(file_path),
                            "size": file_path.stat().st_size,
                            "modified": file_path.stat().st_mtime,
                        }
                    )
        except Exception as e:
            # Skip files that can't be read
            print(f"Warning: Could not read {file_path.name}: {e}")
            continue

    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: x["modified"], reverse=True)

    return log_files


@app.route("/")
def index():
    """Main page - show log file selector"""
    return render_template("index.html")


@app.route("/api/logs")
def api_logs():
    """API endpoint to get available log files"""
    logs = get_available_logs()
    return jsonify(logs)


@app.route("/api/load/<filename>")
def api_load_log(filename):
    """API endpoint to load a specific log file"""
    global current_game, game_data_cache

    logs_dir = get_game_logs_directory()
    log_path = logs_dir / filename

    if not log_path.exists():
        return jsonify({"error": "Log file not found"}), 404

    # Check cache
    if filename in game_data_cache:
        parsed_data = game_data_cache[filename]
    else:
        # Parse the log file
        try:
            parser = GameLogParser(str(log_path))
            parsed_data = parser.parse()

            # Check if game completed normally
            if not parsed_data["game_info"].get("game_completed", False):
                return jsonify({"error": "This game did not complete normally"}), 400

            game_data_cache[filename] = parsed_data
        except Exception as e:
            return jsonify({"error": f"Failed to parse log file: {str(e)}"}), 500

    # Create state manager
    current_game = GameStateManager(parsed_data)

    return jsonify(
        {
            "success": True,
            "game_info": parsed_data["game_info"],
            "players": {
                name: {
                    "name": p.name,
                    "role": p.role,
                    "status": p.status,
                    "death_round": p.death_round,
                    "death_reason": p.death_reason,
                }
                for name, p in parsed_data["players"].items()
            },
            "total_events": len(parsed_data["events"]),
        }
    )


@app.route("/api/state")
def api_get_state():
    """Get current game state"""
    global current_game

    if current_game is None:
        return jsonify({"error": "No game loaded"}), 400

    state = current_game.get_current_state()

    # Convert event to dict if it exists
    if state["current_event"]:
        event = state["current_event"]
        state["current_event"] = {
            "round_num": event.round_num,
            "phase": event.phase,
            "event_type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp,
        }

    return jsonify(state)


@app.route("/api/next")
def api_next_event():
    """Move to next event"""
    global current_game

    if current_game is None:
        return jsonify({"error": "No game loaded"}), 400

    state = current_game.next_event()

    # Convert event to dict
    if state["current_event"]:
        event = state["current_event"]
        state["current_event"] = {
            "round_num": event.round_num,
            "phase": event.phase,
            "event_type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp,
        }

    return jsonify(state)


@app.route("/api/prev")
def api_prev_event():
    """Move to previous event"""
    global current_game

    if current_game is None:
        return jsonify({"error": "No game loaded"}), 400

    state = current_game.prev_event()

    # Convert event to dict
    if state["current_event"]:
        event = state["current_event"]
        state["current_event"] = {
            "round_num": event.round_num,
            "phase": event.phase,
            "event_type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp,
        }

    return jsonify(state)


@app.route("/api/jump/<int:event_index>")
def api_jump_to_event(event_index):
    """Jump to specific event"""
    global current_game

    if current_game is None:
        return jsonify({"error": "No game loaded"}), 400

    state = current_game.jump_to_event(event_index)

    # Convert event to dict
    if state["current_event"]:
        event = state["current_event"]
        state["current_event"] = {
            "round_num": event.round_num,
            "phase": event.phase,
            "event_type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp,
        }

    return jsonify(state)


@app.route("/api/reset")
def api_reset():
    """Reset to beginning"""
    global current_game

    if current_game is None:
        return jsonify({"error": "No game loaded"}), 400

    state = current_game.reset()

    # Convert event to dict
    if state["current_event"]:
        event = state["current_event"]
        state["current_event"] = {
            "round_num": event.round_num,
            "phase": event.phase,
            "event_type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp,
        }

    return jsonify(state)


@app.route("/api/overview")
def api_game_overview():
    """Get comprehensive game overview for quick analysis"""
    global current_game

    if current_game is None:
        return jsonify({"error": "No game loaded"}), 400

    # Get the parsed game data
    game_data = current_game.parsed_data

    # Build comprehensive overview
    overview = {
        "game_info": game_data["game_info"],
        "players": {},
        "round_summary": [],
        "death_timeline": [],
        "voting_history": [],
        "special_actions": [],
        "final_result": {},
    }

    # Enhanced player information
    for name, player in game_data["players"].items():
        overview["players"][name] = {
            "name": player.name,
            "role": player.role,
            "final_status": player.status,
            "death_round": player.death_round,
            "death_reason": player.death_reason,
            "actions_taken": [],
            "votes_cast": [],
            "votes_received": [],
        }

    # Analyze all events to build comprehensive timeline
    current_round = 0
    current_phase = ""
    round_events = []

    for event in game_data["events"]:
        # Track round changes
        if event.round_num != current_round:
            if round_events:
                overview["round_summary"].append(
                    {"round": current_round, "events": round_events.copy()}
                )
            current_round = event.round_num
            round_events = []

        # Collect round events
        round_events.append(
            {"phase": event.phase, "type": event.event_type, "data": event.data}
        )

        # Track deaths
        if event.event_type == "death_announcement" and event.data.get("player"):
            death_info = {
                "round": event.round_num,
                "phase": event.phase,
                "player": event.data["player"],
                "reason": event.data.get("reason", "unknown"),
            }
            overview["death_timeline"].append(death_info)

        # Track voting
        if (
            event.event_type == "vote"
            and event.data.get("voter")
            and event.data.get("target")
        ):
            voter = event.data["voter"]
            target = event.data["target"]

            vote_info = {"round": event.round_num, "voter": voter, "target": target}
            overview["voting_history"].append(vote_info)

            # Add to player vote tracking
            if voter in overview["players"]:
                overview["players"][voter]["votes_cast"].append(
                    {"round": event.round_num, "target": target}
                )
            if target in overview["players"]:
                overview["players"][target]["votes_received"].append(
                    {"round": event.round_num, "voter": voter}
                )

        # Track special actions
        if event.event_type in [
            "werewolf_target",
            "seer_check",
            "witch_save",
            "witch_poison",
            "hunter_skill",
        ]:
            action_info = {
                "round": event.round_num,
                "phase": event.phase,
                "type": event.event_type,
                "actor": event.data.get("player", "unknown"),
                "target": event.data.get("target", ""),
                "result": event.data.get("result", ""),
            }
            overview["special_actions"].append(action_info)

            # Add to player action tracking
            actor = action_info["actor"]
            if actor in overview["players"]:
                overview["players"][actor]["actions_taken"].append(
                    {
                        "round": event.round_num,
                        "action": event.event_type,
                        "target": action_info["target"],
                        "result": action_info["result"],
                    }
                )

    # Add final round if exists
    if round_events:
        overview["round_summary"].append(
            {"round": current_round, "events": round_events}
        )

    # Determine final result
    overview["final_result"] = {
        "winner": game_data["game_info"].get("winner", "unknown"),
        "rounds_played": game_data["game_info"].get("rounds_played", 0),
        "game_completed": game_data["game_info"].get("game_completed", False),
        "werewolves_remaining": len(
            [
                p
                for p in overview["players"].values()
                if p["role"] == "werewolf" and p["final_status"] == "alive"
            ]
        ),
        "villagers_remaining": len(
            [
                p
                for p in overview["players"].values()
                if p["role"] != "werewolf" and p["final_status"] == "alive"
            ]
        ),
    }

    return jsonify(overview)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
