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
    """Get list of available game log files"""
    logs_dir = get_game_logs_directory()

    if not logs_dir.exists():
        return []

    log_files = []
    for file_path in logs_dir.glob("*.txt"):
        log_files.append(
            {
                "filename": file_path.name,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
            }
        )

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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
