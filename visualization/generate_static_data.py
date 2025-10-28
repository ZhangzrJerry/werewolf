#!/usr/bin/env python3
"""
Static data generator for werewolf game visualization
Converts dynamic Flask app data to static JSON files for deployment
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any
import argparse
from dataclasses import asdict

from parser import GameLogParser
from state_manager import GameStateManager


class StaticDataGenerator:
    def __init__(self, output_dir: str = "build", base_url: str = ""):
        self.output_dir = Path(output_dir)
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present
        self.data_dir = self.output_dir / "data"
        self.games_dir = self.data_dir / "games"
        self.learning_dir = self.data_dir / "learning"

        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.games_dir.mkdir(exist_ok=True)
        self.learning_dir.mkdir(exist_ok=True)

    def get_asset_url(self, path: str) -> str:
        """Get URL for an asset with base URL consideration"""
        if self.base_url:
            return f"{self.base_url}/{path}"
        return path

    def get_training_directory(self):
        """获取.training目录路径，优先使用static中的版本"""
        base_dir = Path(__file__).parent

        # 首先检查static/source_files目录中是否有数据（部署版本）
        static_source_files = base_dir / "static" / "source_files"
        if (
            static_source_files.exists()
            and (static_source_files / "strategies").exists()
        ):
            return static_source_files

        # 然后检查static目录中是否有.training
        static_training = base_dir / "static" / ".training"
        if static_training.exists():
            return static_training

        # 如果没有，使用项目根目录的.training
        project_training = base_dir.parent / ".training"
        return project_training

    def get_game_logs_directory(self):
        """Get the path to the game logs directory"""
        base_dir = Path(__file__).parent

        # 首先检查static目录中是否有game_logs（部署版本）
        static_logs = base_dir / "static" / "game_logs"
        if static_logs.exists():
            return static_logs

        # 如果没有，使用training目录中的
        training_dir = self.get_training_directory()
        logs_dir = training_dir / "game_logs"
        return logs_dir

    def get_available_logs(self):
        """Get list of available game log files (only completed games)"""
        logs_dir = self.get_game_logs_directory()

        if not logs_dir.exists():
            print(f"Game logs directory not found: {logs_dir}")
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

    def serialize_game_event(self, event):
        """Convert GameEvent object to serializable dict"""
        return {
            "round_num": event.round_num,
            "phase": event.phase,
            "event_type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp,
        }

    def serialize_player(self, player):
        """Convert Player object to serializable dict"""
        return {
            "name": player.name,
            "role": player.role,
            "status": player.status,
            "death_round": player.death_round,
            "death_reason": player.death_reason,
        }

    def generate_game_data(self, log_file_info: Dict) -> Dict[str, Any]:
        """Generate complete game data for a single game"""
        log_path = log_file_info["path"]
        filename = log_file_info["filename"]
        game_id = Path(filename).stem

        print(f"Processing game: {filename}")

        try:
            # Parse the log file
            parser = GameLogParser(log_path)
            parsed_data = parser.parse()

            # Check if game completed normally
            if not parsed_data["game_info"].get("game_completed", False):
                print(f"Skipping incomplete game: {filename}")
                return None

            # Create state manager for additional data
            state_manager = GameStateManager(parsed_data)

            # Serialize events and players
            serialized_events = [
                self.serialize_game_event(event) for event in parsed_data["events"]
            ]

            serialized_players = {
                name: self.serialize_player(player)
                for name, player in parsed_data["players"].items()
            }

            # Get initial state and serialize current_event if present
            initial_state = state_manager.get_current_state()
            if initial_state.get("current_event"):
                initial_state["current_event"] = self.serialize_game_event(
                    initial_state["current_event"]
                )

            # Build complete game data
            game_data = {
                "id": game_id,
                "filename": filename,
                "game_info": parsed_data["game_info"],
                "players": serialized_players,
                "events": serialized_events,
                "initial_state": initial_state,
                "metadata": {
                    "total_events": len(serialized_events),
                    "file_size": log_file_info["size"],
                    "created": log_file_info["modified"],
                    "generated_at": __import__("time").time(),
                },
            }

            return game_data

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            return None

    def generate_games_list(self, log_files: List[Dict]) -> List[Dict]:
        """Generate games list with metadata"""
        games_list = []

        for log_file_info in log_files:
            filename = log_file_info["filename"]
            game_id = Path(filename).stem

            # Extract basic info from filename or log content if needed
            games_list.append(
                {
                    "id": game_id,
                    "filename": filename,
                    "title": f"Game {game_id}",
                    "created": log_file_info["modified"],
                    "size": log_file_info["size"],
                }
            )

        return games_list

    def get_role_learning_data(self, role: str):
        """获取指定角色的学习数据（移植自app.py）"""
        training_dir = self.get_training_directory()
        reviews_dir = training_dir / "reviews"
        strategies_dir = training_dir / "strategies"

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

                    formatted_date = (
                        f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    )
                    formatted_time = (
                        f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                    )

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
                                if self.is_role_relevant_review(review, role):
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
                                    if content and self.is_role_relevant_review(
                                        content, role
                                    ):
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
            "role": role,
            "sessions": learning_sessions,
            "total_sessions": len(learning_sessions),
            "total_reviews": total_reviews,
            "total_strategies": total_strategies,
        }

    def is_role_relevant_review(self, content: str, role: str) -> bool:
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

    def generate_learning_data(self):
        """Generate learning chain data for all roles"""
        roles = ["seer", "werewolf", "witch", "villager", "guardian", "hunter"]

        for role in roles:
            print(f"Processing learning data for role: {role}")
            learning_data = self.get_role_learning_data(role)

            # Save to JSON file
            output_file = self.learning_dir / f"{role}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(learning_data, f, ensure_ascii=False, indent=2)

            print(f"Saved learning data: {output_file}")

    def copy_static_assets(self):
        """Copy static assets to build directory"""
        static_dir = Path(__file__).parent / "static"

        if static_dir.exists():
            # Copy specific files/directories
            assets_to_copy = [
                "style.css",
                "doc.html",
                "doc.md",
                "teaser-modified.png",
                "public",
            ]

            for asset in assets_to_copy:
                src_path = static_dir / asset
                if src_path.exists():
                    if src_path.is_file():
                        shutil.copy2(src_path, self.output_dir / asset)
                    else:
                        dst_path = self.output_dir / asset
                        if dst_path.exists():
                            shutil.rmtree(dst_path)
                        shutil.copytree(src_path, dst_path)
                    print(f"Copied asset: {asset}")

            # Handle script.js separately to modify API paths
            script_src = static_dir / "script.js"
            if script_src.exists():
                self.copy_and_modify_script(script_src)

    def copy_and_modify_script(self, script_src: Path):
        """Copy and modify script.js to work with static data"""
        with open(script_src, "r", encoding="utf-8") as f:
            content = f.read()

        # Add base URL configuration at the top
        base_url_config = f"""// Static site configuration
const BASE_URL = '{self.base_url}';
const DATA_BASE_URL = BASE_URL ? `${{BASE_URL}}/data` : 'data';

"""

        # Replace API calls with static data loading
        # Replace /api/logs with data/games.json
        content = content.replace(
            "const response = await fetch('/api/logs');",
            "const response = await fetch(`${DATA_BASE_URL}/games.json`);",
        )

        # Replace /api/load/<filename> with data/games/<game_id>.json
        content = content.replace(
            "const response = await fetch(`/api/load/${filename}`);",
            "const gameId = filename.replace('.txt', ''); const response = await fetch(`${DATA_BASE_URL}/games/${gameId}.json`);",
        )

        # Add base URL to other asset references if needed
        content = base_url_config + content

        script_dst = self.output_dir / "script.js"
        with open(script_dst, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Modified and copied script: script.js")

    def convert_template_to_static(self, template_path: Path, output_path: Path):
        """Convert Jinja2 template to static HTML"""
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove Flask template syntax and replace with static paths
        # Replace url_for calls with direct paths (considering base URL)
        content = content.replace(
            "{{ url_for('static', filename='teaser-modified.png') }}",
            self.get_asset_url("teaser-modified.png"),
        )
        content = content.replace(
            "{{ url_for('static', filename='style.css') }}",
            self.get_asset_url("style.css"),
        )
        content = content.replace(
            "{{ url_for('static', filename='script.js') }}",
            self.get_asset_url("script.js"),
        )
        content = content.replace("static/doc.html", self.get_asset_url("doc.html"))

        # For learning chain links, convert to static pages
        content = content.replace(
            'href="learning-chain/seer"',
            f'href="{self.get_asset_url("learning-chain-seer.html")}"',
        )
        content = content.replace(
            'href="learning-chain/werewolf"',
            f'href="{self.get_asset_url("learning-chain-werewolf.html")}"',
        )
        content = content.replace(
            'href="learning-chain/witch"',
            f'href="{self.get_asset_url("learning-chain-witch.html")}"',
        )
        content = content.replace(
            'href="learning-chain/villager"',
            f'href="{self.get_asset_url("learning-chain-villager.html")}"',
        )
        content = content.replace(
            'href="learning-chain/guardian"',
            f'href="{self.get_asset_url("learning-chain-guardian.html")}"',
        )
        content = content.replace(
            'href="learning-chain/hunter"',
            f'href="{self.get_asset_url("learning-chain-hunter.html")}"',
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def generate_learning_chain_pages(self):
        """Generate individual learning chain pages for each role"""
        template_path = Path(__file__).parent / "templates" / "learning_chain.html"

        if not template_path.exists():
            print("Learning chain template not found")
            return

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        roles = [
            {"key": "seer", "name": "预言家", "icon": "🔮"},
            {"key": "werewolf", "name": "狼人", "icon": "🐺"},
            {"key": "witch", "name": "女巫", "icon": "🧙‍♀️"},
            {"key": "villager", "name": "村民", "icon": "👨‍🌾"},
            {"key": "guardian", "name": "守卫", "icon": "🛡️"},
            {"key": "hunter", "name": "猎人", "icon": "🏹"},
        ]

        for role in roles:
            # Replace template variables with actual values
            page_content = template_content
            page_content = page_content.replace("{{ role }}", role["key"])
            page_content = page_content.replace("{{ role_name }}", role["name"])
            page_content = page_content.replace("{{ role_icon }}", role["icon"])

            # Replace static asset paths (considering base URL)
            page_content = page_content.replace(
                "{{ url_for('static', filename='style.css') }}",
                self.get_asset_url("style.css"),
            )
            page_content = page_content.replace(
                "{{ url_for('static', filename='teaser-modified.png') }}",
                self.get_asset_url("teaser-modified.png"),
            )

            # Replace template loops and conditions with static content placeholder
            # This is a simplified approach - in a full implementation, you'd want to
            # actually render the learning data here
            page_content = page_content.replace(
                "{% for session in learning_data %}",
                "<!-- Learning data will be loaded via JavaScript -->",
            )
            page_content = page_content.replace("{% endfor %}", "")
            page_content = page_content.replace("{{ total_sessions }}", "0")
            page_content = page_content.replace("{{ total_reviews }}", "0")
            page_content = page_content.replace("{{ total_strategies }}", "0")

            # Save the page
            output_file = self.output_dir / f"learning-chain-{role['key']}.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(page_content)

            print(f"Generated learning chain page: {output_file}")

    def copy_templates_as_static(self):
        """Convert and copy template files as static HTML"""
        templates_dir = Path(__file__).parent / "templates"

        if templates_dir.exists():
            # Convert index.html
            index_template = templates_dir / "index.html"
            if index_template.exists():
                index_output = self.output_dir / "index.html"
                self.convert_template_to_static(index_template, index_output)
                print(f"Converted template: index.html")

            # Generate learning chain pages
            self.generate_learning_chain_pages()

    def generate_all(self):
        """Generate all static data"""
        print("Starting static data generation...")

        # Get available log files
        log_files = self.get_available_logs()
        print(f"Found {len(log_files)} game log files")

        if not log_files:
            print("No game log files found. Please check your game logs directory.")
            return

        # Generate games list
        games_list = self.generate_games_list(log_files)

        # Generate individual game data
        successful_games = []
        for log_file_info in log_files:
            game_data = self.generate_game_data(log_file_info)
            if game_data:
                # Save individual game data
                game_file = self.games_dir / f"{game_data['id']}.json"
                with open(game_file, "w", encoding="utf-8") as f:
                    json.dump(game_data, f, ensure_ascii=False, indent=2)

                successful_games.append(
                    {
                        "id": game_data["id"],
                        "filename": game_data["filename"],
                        "title": f"Game {game_data['id']}",
                        "created": game_data["metadata"]["created"],
                        "size": game_data["metadata"]["file_size"],
                        "total_events": game_data["metadata"]["total_events"],
                        "winner": game_data["game_info"].get("winner", "unknown"),
                        "rounds": game_data["game_info"].get("rounds_played", 0),
                    }
                )

                print(f"Generated game data: {game_file}")

        # Save games list
        games_list_file = self.data_dir / "games.json"
        with open(games_list_file, "w", encoding="utf-8") as f:
            json.dump(successful_games, f, ensure_ascii=False, indent=2)
        print(f"Generated games list: {games_list_file}")

        # Generate learning data
        self.generate_learning_data()

        # Copy static assets
        self.copy_static_assets()

        # Copy templates
        self.copy_templates_as_static()

        print(f"\nStatic data generation completed!")
        print(f"Output directory: {self.output_dir.absolute()}")
        print(f"Generated {len(successful_games)} game files")
        print(f"Generated learning data for 6 roles")


def main():
    parser = argparse.ArgumentParser(
        description="Generate static data for werewolf visualization"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="build",
        help="Output directory for generated static files (default: build)",
    )
    parser.add_argument(
        "--base-url",
        "-b",
        default="",
        help="Base URL for deployment (e.g., '/werewolf' for GitHub Pages)",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean output directory before generating"
    )

    args = parser.parse_args()

    # Clean output directory if requested
    if args.clean and Path(args.output).exists():
        shutil.rmtree(args.output)
        print(f"Cleaned output directory: {args.output}")

    # Generate static data with base URL
    base_url = args.base_url or ""
    if base_url and not base_url.startswith("/"):
        base_url = "/" + base_url

    generator = StaticDataGenerator(args.output, base_url)
    generator.generate_all()


if __name__ == "__main__":
    main()
