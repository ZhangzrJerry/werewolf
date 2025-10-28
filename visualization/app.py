from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import json
import re
from pathlib import Path
from parser import GameLogParser
from state_manager import GameStateManager

app = Flask(__name__)

# Store current game state manager
current_game = None
current_game_filename = None
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


# Reviews helper functions
def get_reviews_directory():
    """Return the reviews base directory path"""
    base_dir = Path(__file__).parent.parent
    return base_dir / ".training" / "reviews"


def find_review_folder_for_log(log_path: Path):
    """Find the best-matching review folder for a given log file.

    Strategy:
    - If a folder name substring appears in the log filename, prefer that folder.
    - Otherwise choose the review folder with modification time closest to the log file's mtime.
    Returns Path or None.
    """
    reviews_dir = get_reviews_directory()
    if not reviews_dir.exists():
        return None

    # Try to match by timestamp fragment present in filename
    fname = log_path.name if log_path else ""
    for sub in reviews_dir.iterdir():
        if not sub.is_dir():
            continue
        if sub.name in fname:
            return sub

    # Fallback: pick folder with closest mtime to log file
    try:
        log_mtime = log_path.stat().st_mtime if log_path.exists() else None
    except Exception:
        log_mtime = None

    best = None
    best_diff = None
    for sub in reviews_dir.iterdir():
        if not sub.is_dir():
            continue
        try:
            sub_mtime = sub.stat().st_mtime
        except Exception:
            continue
        if log_mtime is None:
            # if we don't have log mtime, prefer latest review
            if best is None or sub_mtime > best.stat().st_mtime:
                best = sub
            continue

        diff = abs(sub_mtime - log_mtime)
        if best is None or diff < best_diff:
            best = sub
            best_diff = diff

    return best


def read_reviews_from_folder(folder: Path):
    """Read review artifacts from a folder. Returns a dict or None."""
    if folder is None:
        return None

    result = {}
    try:
        full_json = folder / "full_analysis.json"
        lessons_json = folder / "lessons.json"
        overall_txt = folder / "overall.txt"

        if full_json.exists():
            with open(full_json, "r", encoding="utf-8") as f:
                result["full_analysis"] = json.load(f)

        if lessons_json.exists():
            with open(lessons_json, "r", encoding="utf-8") as f:
                try:
                    result["lessons"] = json.load(f)
                except Exception:
                    result["lessons_text"] = f.read()

        if overall_txt.exists():
            with open(overall_txt, "r", encoding="utf-8") as f:
                result["overall_text"] = f.read()

        # include per-player review files if present
        reviews = {}
        for pfile in folder.iterdir():
            if pfile.is_file() and pfile.name.endswith("_review.txt"):
                pname = pfile.name.replace("_review.txt", "")
                with open(pfile, "r", encoding="utf-8") as f:
                    reviews[pname] = f.read()
        if reviews:
            result["per_player"] = reviews

        # if we found anything, return
        return result if result else None
    except Exception as e:
        print(f"Failed to read reviews from {folder}: {e}")
        return None


def get_role_learning_data(role):
    """获取指定角色的学习数据"""
    base_dir = Path(__file__).parent.parent
    reviews_dir = base_dir / ".training" / "reviews"
    strategies_dir = base_dir / ".training" / "strategies"

    learning_sessions = []
    total_reviews = 0
    total_strategies = 0

    # 获取策略文件中的所有策略
    strategy_file = strategies_dir / f"{role}.json"
    current_strategies = []
    if strategy_file.exists():
        try:
            with open(strategy_file, "r", encoding="utf-8") as f:
                strategy_data = json.load(f)
                current_strategies = strategy_data.get("rules", [])
                total_strategies = len(current_strategies)
        except Exception as e:
            print(f"Error reading strategy file for {role}: {e}")

    # 遍历所有复盘会话
    if reviews_dir.exists():
        session_dirs = sorted(
            [d for d in reviews_dir.iterdir() if d.is_dir()],
            key=lambda x: x.name,
            reverse=True,
        )

        for session_dir in session_dirs:
            try:
                # 解析时间戳
                timestamp = session_dir.name
                date_part = timestamp[:8]  # YYYYMMDD
                time_part = timestamp[9:]  # HHMMSS

                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                formatted_time = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"

                # 收集该会话的复盘记录
                session_reviews = []
                session_strategies = []

                # 首先尝试从full_analysis.json获取结构化数据
                full_analysis_file = session_dir / "full_analysis.json"
                if full_analysis_file.exists():
                    try:
                        with open(full_analysis_file, "r", encoding="utf-8") as f:
                            analysis_data = json.load(f)

                        # 获取角色相关的复盘记录
                        per_player = analysis_data.get("per_player", {})
                        for player, review in per_player.items():
                            if is_role_relevant_review(review, role):
                                session_reviews.append(
                                    {"player": player, "content": review}
                                )

                        # 获取角色相关的lessons作为策略
                        lessons = analysis_data.get("lessons", {})
                        role_key = role.capitalize()  # 首字母大写匹配JSON中的格式
                        if role_key in lessons:
                            session_strategies = lessons[role_key][:5]  # 取前5条

                    except Exception as e:
                        print(
                            f"Error reading full_analysis.json in {session_dir.name}: {e}"
                        )

                # 如果没有从full_analysis获取到数据，则从单独的review文件获取
                if not session_reviews:
                    for review_file in session_dir.glob("*_review.txt"):
                        player_name = review_file.name.replace("_review.txt", "")
                        try:
                            with open(review_file, "r", encoding="utf-8") as f:
                                content = f.read().strip()
                                if content and is_role_relevant_review(content, role):
                                    session_reviews.append(
                                        {"player": player_name, "content": content}
                                    )
                        except Exception as e:
                            print(f"Error reading review file {review_file}: {e}")

                # 如果没有会话特定的策略，使用当前策略的一部分
                if not session_strategies and current_strategies:
                    session_strategies = current_strategies[:3]

                total_reviews += len(session_reviews)

                # 只有有数据时才添加会话
                if session_reviews or session_strategies:
                    learning_sessions.append(
                        {
                            "date": formatted_date,
                            "time": formatted_time,
                            "reviews": session_reviews,
                            "strategies": session_strategies,
                            "timestamp": timestamp,
                        }
                    )

            except Exception as e:
                print(f"Error processing session {session_dir.name}: {e}")

    return {
        "sessions": learning_sessions,
        "total_sessions": len(learning_sessions),
        "total_reviews": total_reviews,
        "total_strategies": total_strategies,
    }


def is_role_relevant_review(content, role):
    """判断复盘内容是否与指定角色相关"""
    role_keywords = {
        "seer": ["预言家", "seer", "查验", "验人", "警徽"],
        "werewolf": ["狼人", "werewolf", "刀人", "狼队"],
        "witch": ["女巫", "witch", "毒药", "解药"],
        "villager": ["村民", "villager", "票型", "发言"],
        "guardian": ["守卫", "guardian", "守护", "撞刀"],
        "hunter": ["猎人", "hunter", "开枪", "带走"],
    }

    keywords = role_keywords.get(role, [])
    content_lower = content.lower()

    return any(keyword.lower() in content_lower for keyword in keywords)


@app.route("/")
def index():
    """Main page - show log file selector"""
    return render_template("index.html")


@app.route("/learning-chain/<role>")
def learning_chain(role):
    """学习链页面 - 显示指定角色的学习历程"""
    role_config = {
        "seer": {"name": "预言家", "icon": "🔮"},
        "werewolf": {"name": "狼人", "icon": "🐺"},
        "witch": {"name": "女巫", "icon": "🧙‍♀️"},
        "villager": {"name": "村民", "icon": "👨‍🌾"},
        "guardian": {"name": "守卫", "icon": "🛡️"},
        "hunter": {"name": "猎人", "icon": "🏹"},
    }

    if role not in role_config:
        return "角色不存在", 404

    learning_data = get_role_learning_data(role)

    return render_template(
        "learning_chain.html",
        role=role,
        role_name=role_config[role]["name"],
        role_icon=role_config[role]["icon"],
        learning_data=learning_data["sessions"],
        total_sessions=learning_data["total_sessions"],
        total_reviews=learning_data["total_reviews"],
        total_strategies=learning_data["total_strategies"],
    )


@app.route("/api/logs")
def api_logs():
    """API endpoint to get available log files"""
    logs = get_available_logs()
    return jsonify(logs)


@app.route("/api/load/<filename>")
def api_load_log(filename):
    """Load a specific log file"""
    global current_game, current_game_filename

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

    # Create state manager and store filename
    current_game = GameStateManager(parsed_data)
    current_game_filename = filename

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


def generate_game_reviews_and_lessons(overview):
    """Generate comprehensive game analysis with reviews and lessons"""
    analysis = {
        "game_summary": "",
        "key_turning_points": [],
        "player_performance": {},
        "strategic_insights": [],
        "lessons_learned": [],
        "mvp_analysis": "",
        "critical_mistakes": [],
    }

    # Game summary
    winner = overview["final_result"]["winner"]
    rounds = overview["final_result"]["rounds_played"]
    werewolves_left = overview["final_result"]["werewolves_remaining"]
    villagers_left = overview["final_result"]["villagers_remaining"]

    analysis["game_summary"] = (
        f"经过{rounds}回合的激烈角逐，{winner}方获得胜利。"
        + f"最终剩余{werewolves_left}名狼人和{villagers_left}名村民阵营玩家。"
    )

    # Analyze key turning points
    for death in overview["death_timeline"]:
        player_name = death["player"]
        player_info = overview["players"].get(player_name, {})
        role = player_info.get("role", "unknown")

        if role in ["seer", "witch", "hunter"]:
            analysis["key_turning_points"].append(
                {
                    "round": death["round"],
                    "description": f"{role}({player_name})在第{death['round']}回合{death['phase']}死亡",
                    "impact": f"关键角色{role}的死亡显著影响了游戏走向",
                }
            )

    # Player performance analysis
    for name, player in overview["players"].items():
        performance = {
            "survival_rounds": player.get("death_round", rounds + 1) - 1,
            "votes_cast_count": len(player.get("votes_cast", [])),
            "votes_received_count": len(player.get("votes_received", [])),
            "actions_taken_count": len(player.get("actions_taken", [])),
            "performance_rating": "一般",
        }

        # Rate performance based on survival and activity
        if player["final_status"] == "alive":
            if player["role"] == "werewolf":
                performance["performance_rating"] = (
                    "优秀" if winner == "werewolf" else "良好"
                )
            else:
                performance["performance_rating"] = (
                    "优秀" if winner == "villager" else "良好"
                )
        else:
            if performance["survival_rounds"] > rounds * 0.7:
                performance["performance_rating"] = "良好"
            elif performance["survival_rounds"] < rounds * 0.3:
                performance["performance_rating"] = "需改进"

        analysis["player_performance"][name] = performance

    # Strategic insights
    werewolf_players = [
        p for p in overview["players"].values() if p["role"] == "werewolf"
    ]
    if len(werewolf_players) > 0:
        werewolf_survival_rate = len(
            [p for p in werewolf_players if p["final_status"] == "alive"]
        ) / len(werewolf_players)
        if werewolf_survival_rate > 0.5:
            analysis["strategic_insights"].append("狼人团队协作良好，伪装能力较强")
        else:
            analysis["strategic_insights"].append("狼人暴露较早，可能存在策略失误")

    # Lessons learned based on game outcome
    if winner == "werewolf":
        analysis["lessons_learned"].extend(
            [
                "村民方需要更好地利用信息和逻辑推理",
                "神职角色的保护和配合需要加强",
                "投票时需要更加谨慎，避免误投关键角色",
            ]
        )
    else:
        analysis["lessons_learned"].extend(
            [
                "狼人需要提高伪装技巧和团队配合",
                "夜间击杀目标的选择很关键",
                "白天发言要更加谨慎，避免露出破绽",
            ]
        )

    # MVP analysis
    survivors = [
        p for p in overview["players"].values() if p["final_status"] == "alive"
    ]
    if survivors:
        mvp_candidate = max(
            survivors,
            key=lambda p: analysis["player_performance"][p["name"]]["survival_rounds"],
        )
        analysis["mvp_analysis"] = (
            f"本局MVP候选: {mvp_candidate['name']}({mvp_candidate['role']}) - 存活到最后且表现优异"
        )

    # Critical mistakes analysis
    early_deaths = [d for d in overview["death_timeline"] if d["round"] <= 2]
    for death in early_deaths:
        player_name = death["player"]
        player_info = overview["players"].get(player_name, {})
        if player_info.get("role") in ["seer", "witch"]:
            analysis["critical_mistakes"].append(
                {
                    "description": f"{player_info['role']}过早死亡",
                    "impact": "关键神职角色保护不足",
                    "lesson": "神职角色需要更加低调，村民要提供更好保护",
                }
            )

    return analysis


def extract_performance_rating(review_text):
    """Extract performance rating from review text."""
    if not review_text:
        return "good"

    review_lower = review_text.lower()
    if any(word in review_lower for word in ["优秀", "excellent", "杰出", "出色"]):
        return "优秀"
    elif any(word in review_lower for word in ["差", "poor", "糟糕", "失误", "错误"]):
        return "需改进"
    else:
        return "良好"


def transform_reviews_to_frontend_format(reviews_data, overview_data=None):
    """Transform loaded review data from disk format to frontend-expected format."""
    transformed = {}

    # Extract overall game summary
    if "overall_text" in reviews_data:
        transformed["game_summary"] = reviews_data["overall_text"]
    elif "full_analysis" in reviews_data and "overall" in reviews_data["full_analysis"]:
        transformed["game_summary"] = reviews_data["full_analysis"]["overall"]

    # Extract per-player reviews and transform to player_performance format
    player_perf = {}

    # First, get player statistics from overview if available
    if overview_data and "players" in overview_data:
        for player_name, player_data in overview_data["players"].items():
            player_perf[player_name] = {
                "performance_rating": "good",
                "survival_rounds": calculate_survival_rounds(player_data),
                "votes_cast_count": len(player_data.get("votes_cast", [])),
                "votes_received_count": len(player_data.get("votes_received", [])),
                "review": "",  # Will be filled from review data
            }

    # Then add review text from saved files and extract performance rating
    if "per_player" in reviews_data:
        for player_name, review_text in reviews_data["per_player"].items():
            if player_name not in player_perf:
                player_perf[player_name] = {
                    "performance_rating": "good",
                    "survival_rounds": 0,
                    "votes_cast_count": 0,
                    "votes_received_count": 0,
                }
            player_perf[player_name]["review"] = review_text
            # Extract performance rating from review text
            player_perf[player_name]["performance_rating"] = extract_performance_rating(
                review_text
            )
    elif (
        "full_analysis" in reviews_data
        and "per_player" in reviews_data["full_analysis"]
    ):
        for player_name, review_text in reviews_data["full_analysis"][
            "per_player"
        ].items():
            if player_name not in player_perf:
                player_perf[player_name] = {
                    "performance_rating": "good",
                    "survival_rounds": 0,
                    "votes_cast_count": 0,
                    "votes_received_count": 0,
                }
            player_perf[player_name]["review"] = review_text
            # Extract performance rating from review text
            player_perf[player_name]["performance_rating"] = extract_performance_rating(
                review_text
            )

    transformed["player_performance"] = player_perf

    # Extract lessons and merge by role type (remove strategic insights section)
    lessons_learned = []

    if "lessons" in reviews_data:
        if isinstance(reviews_data["lessons"], dict):
            for role, tips in reviews_data["lessons"].items():
                if isinstance(tips, list):
                    # Merge all tips for this role into one entry
                    merged_tips = "; ".join(tips)
                    lessons_learned.append(f"{role}: {merged_tips}")
                else:
                    lessons_learned.append(f"{role}: {tips}")
    elif "full_analysis" in reviews_data and "lessons" in reviews_data["full_analysis"]:
        lessons_data = reviews_data["full_analysis"]["lessons"]
        if isinstance(lessons_data, dict):
            for role, tips in lessons_data.items():
                if isinstance(tips, list):
                    # Merge all tips for this role into one entry
                    merged_tips = "; ".join(tips)
                    lessons_learned.append(f"{role}: {merged_tips}")
                else:
                    lessons_learned.append(f"{role}: {tips}")

    # Don't include strategic_insights - remove this section
    transformed["lessons_learned"] = lessons_learned

    # Add some default empty fields that frontend expects
    if "key_turning_points" not in transformed:
        transformed["key_turning_points"] = []
    if "mvp_analysis" not in transformed:
        transformed["mvp_analysis"] = ""
    if "critical_mistakes" not in transformed:
        transformed["critical_mistakes"] = []
    # Remove strategic_insights section - not needed
    if "strategic_insights" not in transformed:
        transformed["strategic_insights"] = []

    return transformed


def calculate_survival_rounds(player_data):
    """Calculate how many rounds a player survived."""
    if player_data.get("final_status") == "alive":
        # Player survived the entire game
        return player_data.get("total_rounds", 0)
    else:
        # Player died, return death round (or 0 if no death round recorded)
        return player_data.get("death_round", 0)


@app.route("/api/overview")
def api_game_overview():
    """Get comprehensive game overview for quick analysis"""
    global current_game, current_game_filename

    if current_game is None:
        return jsonify({"error": "No game loaded"}), 400

    # Get the current log file content
    raw_log_content = ""
    try:
        if current_game_filename:
            logs_dir = get_game_logs_directory()
            log_path = logs_dir / current_game_filename
            if log_path.exists():
                with open(log_path, "r", encoding="utf-8") as f:
                    raw_log_content = f.read()
            else:
                raw_log_content = "日志文件未找到"
        else:
            raw_log_content = "未知日志文件"

    except Exception as e:
        raw_log_content = f"读取日志失败: {str(e)}"

    # Build comprehensive overview
    overview = {
        "game_info": current_game.game_info,
        "raw_log": raw_log_content,
        "players": {},
        "round_summary": [],
        "death_timeline": [],
        "voting_history": [],
        "special_actions": [],
        "final_result": {},
        "reviews_and_lessons": {},
    }

    # Enhanced player information
    total_rounds = current_game.game_info.get("rounds_played", 0)
    for name, player in current_game.players.items():
        overview["players"][name] = {
            "name": player.name,
            "role": player.role,
            "final_status": player.status,
            "death_round": player.death_round,
            "death_reason": player.death_reason,
            "total_rounds": total_rounds,
            "actions_taken": [],
            "votes_cast": [],
            "votes_received": [],
        }

    # Analyze all events to build comprehensive timeline
    current_round = 0
    current_phase = ""
    round_events = []

    for event in current_game.events:
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
            # Extract actor based on event type
            actor = "unknown"
            target = ""
            result = ""

            if event.event_type == "werewolf_target":
                # Handle werewolf targets: {"targets": {werewolf: target, ...}}
                targets = event.data.get("targets", {})
                if targets:
                    # For display purposes, show all werewolf actions
                    for werewolf, werewolf_target in targets.items():
                        action_info = {
                            "round": event.round_num,
                            "phase": event.phase,
                            "type": event.event_type,
                            "actor": werewolf,
                            "target": werewolf_target,
                            "result": "",
                        }
                        overview["special_actions"].append(action_info)

                        # Add to player action tracking
                        if werewolf in overview["players"]:
                            overview["players"][werewolf]["actions_taken"].append(
                                {
                                    "round": event.round_num,
                                    "action": event.event_type,
                                    "target": werewolf_target,
                                    "result": "",
                                }
                            )
                    continue  # Skip the general handling below

            elif event.event_type == "seer_check":
                actor = event.data.get("seer", "unknown")
                target = event.data.get("target", "")
                result = event.data.get("result", "")

            elif event.event_type in ["witch_save", "witch_poison"]:
                actor = event.data.get("witch", "unknown")
                target = event.data.get("target", "")
                if event.event_type == "witch_save":
                    saved = event.data.get("saved", False)
                    result = "已救" if saved else "未救"
                else:  # witch_poison
                    used = event.data.get("used", False)
                    poison_target = event.data.get("poison_target", "")
                    target = poison_target if poison_target else ""
                    result = "已用毒" if used else "未用毒"

            elif event.event_type == "hunter_skill":
                actor = event.data.get("hunter", event.data.get("player", "unknown"))
                target = event.data.get("target", "")
                result = event.data.get("result", "")

            action_info = {
                "round": event.round_num,
                "phase": event.phase,
                "type": event.event_type,
                "actor": actor,
                "target": target,
                "result": result,
            }
            overview["special_actions"].append(action_info)

            # Add to player action tracking
            if actor in overview["players"]:
                overview["players"][actor]["actions_taken"].append(
                    {
                        "round": event.round_num,
                        "action": event.event_type,
                        "target": target,
                        "result": result,
                    }
                )

    # Add final round if exists
    if round_events:
        overview["round_summary"].append(
            {"round": current_round, "events": round_events}
        )

    # Determine final result
    overview["final_result"] = {
        "winner": current_game.game_info.get("winner", "unknown"),
        "rounds_played": current_game.game_info.get("rounds_played", 0),
        "game_completed": current_game.game_info.get("game_completed", False),
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

    # Load reviews and lessons from saved files (fallback to generation)
    try:
        reviews_data = None
        review_folder = None
        if current_game_filename:
            logs_dir = get_game_logs_directory()
            log_path = logs_dir / current_game_filename
            review_folder = find_review_folder_for_log(log_path)
            if review_folder:
                reviews_data = read_reviews_from_folder(review_folder)

        if reviews_data:
            # Transform loaded review data to expected frontend format
            transformed_reviews = transform_reviews_to_frontend_format(
                reviews_data, overview
            )
            overview["reviews_and_lessons"] = transformed_reviews
            overview["reviews_source"] = str(review_folder)
        else:
            # Fallback: generate on-the-fly
            overview["reviews_and_lessons"] = generate_game_reviews_and_lessons(
                overview
            )
            overview["reviews_source"] = "generated"
    except Exception as e:
        print(f"Error loading reviews and lessons: {e}")
        overview["reviews_and_lessons"] = {
            "error": f"加载或生成分析失败: {str(e)}",
            "game_summary": "分析功能暂时不可用",
            "key_turning_points": [],
            "player_performance": {},
            "strategic_insights": [],
            "lessons_learned": [],
            "mvp_analysis": "",
            "critical_mistakes": [],
        }

    return jsonify(overview)


# === API 端点用于静态站点生成 ===


@app.route("/api/games")
def api_games():
    """获取所有可用游戏的列表（用于静态站点生成）"""
    # 优先使用静态文件中的游戏
    static_logs_dir = Path(__file__).parent / "static" / "game_logs"
    if static_logs_dir.exists():
        logs_dir = static_logs_dir
    else:
        logs_dir = get_game_logs_directory()

    if not logs_dir.exists():
        return jsonify([])

    games = []

    # 检查是否有清单文件
    manifest_file = logs_dir / "games_manifest.json"
    if manifest_file.exists():
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                for game_info in manifest.get("games", []):
                    games.append(
                        {
                            "id": game_info["filename"].replace(".txt", ""),
                            "filename": game_info["filename"],
                            "game_type": game_info["game_type"],
                            "player_count": game_info["player_count"],
                            "rounds": game_info["rounds"],
                            "winner": game_info["winner"],
                            "timestamp": game_info["timestamp"],
                        }
                    )
            return jsonify(games)
        except Exception as e:
            print(f"Error reading manifest: {e}")

    # 回退到文件系统扫描
    for file_path in logs_dir.glob("*.txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # 提取基本信息
                game_type_match = re.search(r"Game Type: (\w+)", content)
                game_type = game_type_match.group(1) if game_type_match else "unknown"

                players_match = re.search(r"Players: (.+)", content)
                players = players_match.group(1).split(", ") if players_match else []

                winner_match = re.search(
                    r"(WEREWOLVES WIN|VILLAGERS WIN|DRAW)", content
                )
                winner = winner_match.group(1) if winner_match else "unknown"

                rounds = len(re.findall(r"ROUND \d+", content))

                games.append(
                    {
                        "id": file_path.stem,
                        "filename": file_path.name,
                        "game_type": game_type,
                        "player_count": len(players),
                        "rounds": rounds,
                        "winner": winner,
                        "timestamp": file_path.stat().st_mtime,
                    }
                )
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    # 按时间排序
    games.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify(games)


@app.route("/api/game/<game_id>")
def api_game_data(game_id):
    """获取特定游戏的完整数据（用于静态站点生成）"""
    filename = f"{game_id}.txt"

    # 优先使用静态文件
    static_logs_dir = Path(__file__).parent / "static" / "game_logs"
    if static_logs_dir.exists() and (static_logs_dir / filename).exists():
        log_path = static_logs_dir / filename
    else:
        logs_dir = get_game_logs_directory()
        log_path = logs_dir / filename

    if not log_path.exists():
        return jsonify({"error": "Game not found"}), 404

    try:
        # 检查缓存
        if filename in game_data_cache:
            parsed_data = game_data_cache[filename]
        else:
            parser = GameLogParser(str(log_path))
            parsed_data = parser.parse()
            game_data_cache[filename] = parsed_data

        # 创建临时状态管理器来获取完整数据
        temp_game = GameStateManager(parsed_data)

        # 构建完整的游戏数据
        game_data = {
            "id": game_id,
            "game_info": parsed_data["game_info"],
            "players": parsed_data["players"],
            "events": parsed_data["events"],
            "player_states": temp_game.get_current_state()["players"],
            "reviews": get_game_reviews(game_id),
            "metadata": {
                "total_events": len(parsed_data["events"]),
                "file_size": log_path.stat().st_size,
                "created": log_path.stat().st_mtime,
            },
        }

        return jsonify(game_data)

    except Exception as e:
        return jsonify({"error": f"Failed to load game: {str(e)}"}), 500


def get_game_reviews(game_id):
    """获取游戏的review数据"""
    reviews_dir = Path(__file__).parent / "static" / "source_files" / "reviews"

    if not reviews_dir.exists():
        return []

    reviews = []

    # 查找与游戏相关的review目录
    for review_dir in reviews_dir.iterdir():
        if not review_dir.is_dir():
            continue

        # 检查目录名是否包含游戏ID
        if game_id in review_dir.name or any(
            pattern in review_dir.name.lower()
            for pattern in [
                "seer_learning_analysis",
                "villager_learning_analysis",
                "werewolf_learning_analysis",
                "witch_learning_analysis",
            ]
        ):
            # 收集该目录下的所有markdown文件
            for review_file in review_dir.rglob("*.md"):
                try:
                    with open(review_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    reviews.append(
                        {
                            "type": classify_review_file(review_file.name),
                            "title": review_file.stem.replace("_", " ").title(),
                            "path": str(review_file.relative_to(reviews_dir)),
                            "content": content,
                            "size": len(content),
                        }
                    )
                except Exception as e:
                    print(f"Error reading review file {review_file}: {e}")

    return reviews


def classify_review_file(filename):
    """分类review文件"""
    filename_lower = filename.lower()

    if "seer" in filename_lower:
        return "seer_analysis"
    elif "werewolf" in filename_lower:
        return "werewolf_analysis"
    elif "witch" in filename_lower:
        return "witch_analysis"
    elif "villager" in filename_lower:
        return "villager_analysis"
    elif "guardian" in filename_lower:
        return "guardian_analysis"
    elif "hunter" in filename_lower:
        return "hunter_analysis"
    elif "game_analysis" in filename_lower:
        return "game_analysis"
    elif "strategy" in filename_lower:
        return "strategy_analysis"
    else:
        return "general"


@app.route("/api/reviews")
def api_reviews():
    """获取所有available reviews"""
    reviews_dir = Path(__file__).parent / "static" / "source_files" / "reviews"

    if not reviews_dir.exists():
        return jsonify([])

    reviews_summary = []

    for review_dir in reviews_dir.iterdir():
        if not review_dir.is_dir():
            continue

        review_info = {
            "name": review_dir.name,
            "type": classify_review_dir(review_dir.name),
            "files": [],
            "total_files": 0,
        }

        for review_file in review_dir.rglob("*.md"):
            review_info["files"].append(
                {
                    "name": review_file.name,
                    "path": str(review_file.relative_to(reviews_dir)),
                    "size": review_file.stat().st_size,
                }
            )

        review_info["total_files"] = len(review_info["files"])
        reviews_summary.append(review_info)

    return jsonify(reviews_summary)


@app.route("/api/doc")
def api_doc():
    """提供文档页面"""
    return send_from_directory("static", "doc.html")


@app.route("/api/assets/<path:filename>")
def serve_assets(filename):
    """统一提供静态资源文件"""
    # 支持多个资源目录，按优先级搜索
    asset_dirs = [
        Path(__file__).parent / "static" / "public",
        Path(__file__).parent / "static" / "source_files",
        Path(__file__).parent.parent / "doc" / "public",  # 兼容旧路径
    ]

    for asset_dir in asset_dirs:
        file_path = asset_dir / filename
        if file_path.exists() and file_path.is_file():
            return send_from_directory(str(asset_dir), filename)

    # 如果文件不存在，返回404
    return jsonify({"error": f"Asset '{filename}' not found"}), 404


def classify_review_dir(dirname):
    """分类review目录"""
    dirname_lower = dirname.lower()

    if "seer" in dirname_lower:
        return "seer_analysis"
    elif "werewolf" in dirname_lower:
        return "werewolf_analysis"
    elif "witch" in dirname_lower:
        return "witch_analysis"
    elif "villager" in dirname_lower:
        return "villager_analysis"
    elif "guardian" in dirname_lower:
        return "guardian_analysis"
    elif "hunter" in dirname_lower:
        return "hunter_analysis"
    else:
        return "general"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
