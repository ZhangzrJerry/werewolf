#!/usr/bin/env python3
"""
游戏日志整理脚本
用于GitHub Actions中处理和过滤游戏日志文件
"""

import os
import shutil
import re
from datetime import datetime, timedelta
from pathlib import Path
import json


class GameLogOrganizer:
    def __init__(
        self,
        source_dir=".training/game_logs",
        target_dir="visualization/static/game_logs",
        reviews_source_dir=".training/reviews",
        reviews_target_dir="visualization/static/source_files/reviews",
    ):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.reviews_source_dir = Path(reviews_source_dir)
        self.reviews_target_dir = Path(reviews_target_dir)

        # 创建目标目录
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.reviews_target_dir.mkdir(parents=True, exist_ok=True)

    def extract_game_info(self, log_path):
        """从日志文件中提取游戏信息"""
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取游戏类型
            game_type_match = re.search(r"Game Type: (\w+)", content)
            game_type = game_type_match.group(1) if game_type_match else "unknown"

            # 提取玩家信息
            players_match = re.search(r"Players: (.+)", content)
            players = players_match.group(1).split(", ") if players_match else []

            # 提取狼人队伍
            werewolf_match = re.search(r"Werewolf team: (.+)", content)
            werewolves = werewolf_match.group(1).split(", ") if werewolf_match else []

            # 提取胜利者
            winner_match = re.search(r"(WEREWOLVES WIN|VILLAGERS WIN|DRAW)", content)
            winner = winner_match.group(1) if winner_match else "unknown"

            # 从文件名提取时间
            filename = log_path.name
            time_match = re.search(r"(\d{8}_\d{6})", filename)
            if time_match:
                time_str = time_match.group(1)
                game_time = datetime.strptime(time_str, "%Y%m%d_%H%M%S")
            else:
                game_time = datetime.fromtimestamp(os.path.getmtime(log_path))

            # 计算游戏时长（轮数）
            rounds = len(re.findall(r"ROUND \d+", content))

            return {
                "filename": filename,
                "game_type": game_type,
                "players": players,
                "player_count": len(players),
                "werewolves": werewolves,
                "winner": winner,
                "rounds": rounds,
                "timestamp": game_time.isoformat(),
                "file_size": os.path.getsize(log_path),
                "has_complete_game": "GAME ENDING" in content
                or any(
                    winner in content for winner in ["WEREWOLVES WIN", "VILLAGERS WIN"]
                ),
            }
        except Exception as e:
            print(f"Error processing {log_path}: {e}")
            return None

    def filter_logs(self, max_files=100, min_rounds=3, recent_days=30):
        """过滤日志文件"""
        if not self.source_dir.exists():
            print(f"Source directory {self.source_dir} does not exist")
            return []

        # 获取所有日志文件
        log_files = list(self.source_dir.glob("*.txt"))
        print(f"Found {len(log_files)} log files")

        # 提取文件信息
        file_info = []
        for log_file in log_files:
            info = self.extract_game_info(log_file)
            if info:
                file_info.append((log_file, info))

        # 过滤条件
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        filtered_files = []

        for log_file, info in file_info:
            game_time = datetime.fromisoformat(info["timestamp"])

            # 过滤条件
            if (
                info["has_complete_game"]
                and info["rounds"] >= min_rounds
                and game_time >= cutoff_date
            ):
                filtered_files.append((log_file, info))

        # 按时间排序，取最新的
        filtered_files.sort(key=lambda x: x[1]["timestamp"], reverse=True)
        selected_files = filtered_files[:max_files]

        print(f"Selected {len(selected_files)} files after filtering")
        return selected_files

    def copy_selected_logs(self, selected_files):
        """复制选定的日志文件"""
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "total_files": len(selected_files),
            "games": [],
        }

        for log_file, info in selected_files:
            # 复制文件
            target_file = self.target_dir / log_file.name
            shutil.copy2(log_file, target_file)

            # 查找并复制对应的review文件
            review_info = self.find_and_copy_reviews(log_file, info)
            info["reviews"] = review_info

            # 添加到清单
            manifest["games"].append(info)
            print(f"Copied: {log_file.name}")

        # 保存清单文件
        manifest_file = self.target_dir / "games_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"Game manifest saved to {manifest_file}")
        return len(selected_files)

    def find_and_copy_reviews(self, log_file, game_info):
        """查找并复制对应的review文件"""
        if not self.reviews_source_dir.exists():
            return []

        reviews_info = []
        log_filename = log_file.stem  # 不包含扩展名的文件名

        # 搜索包含游戏ID的review目录和文件
        for review_dir in self.reviews_source_dir.iterdir():
            if not review_dir.is_dir():
                continue

            # 检查目录名是否包含游戏相关信息
            if self.is_review_related_to_game(review_dir.name, log_filename, game_info):
                review_target_dir = self.reviews_target_dir / review_dir.name

                try:
                    # 复制整个review目录
                    if review_target_dir.exists():
                        shutil.rmtree(review_target_dir)
                    shutil.copytree(review_dir, review_target_dir)

                    # 收集review信息
                    review_files = list(review_target_dir.rglob("*.md"))
                    for review_file in review_files:
                        reviews_info.append(
                            {
                                "type": self.classify_review_type(review_file.name),
                                "path": str(
                                    review_file.relative_to(
                                        self.reviews_target_dir.parent
                                    )
                                ),
                                "filename": review_file.name,
                                "size": review_file.stat().st_size,
                            }
                        )

                    print(
                        f"  Copied review: {review_dir.name} ({len(review_files)} files)"
                    )

                except Exception as e:
                    print(f"  Warning: Failed to copy review {review_dir.name}: {e}")

        return reviews_info

    def is_review_related_to_game(self, review_dir_name, log_filename, game_info):
        """判断review目录是否与游戏相关"""
        # 检查时间戳匹配
        time_pattern = re.search(r"(\d{8}_\d{6})", log_filename)
        if time_pattern and time_pattern.group(1) in review_dir_name:
            return True

        # 检查游戏ID匹配（如果有的话）
        game_id_pattern = re.search(r"([a-f0-9]{8})$", log_filename)
        if game_id_pattern and game_id_pattern.group(1) in review_dir_name:
            return True

        # 检查是否是学习链分析（通用类型）
        learning_patterns = [
            "seer_learning_analysis",
            "villager_learning_analysis",
            "werewolf_learning_analysis",
            "witch_learning_analysis",
            "guardian_learning_analysis",
            "hunter_learning_analysis",
        ]

        for pattern in learning_patterns:
            if pattern in review_dir_name.lower():
                return True

        return False

    def classify_review_type(self, filename):
        """分类review文件类型"""
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

    def create_summary_stats(self, selected_files):
        """创建统计摘要"""
        stats = {
            "total_games": len(selected_files),
            "by_game_type": {},
            "by_winner": {},
            "by_player_count": {},
            "average_rounds": 0,
            "date_range": {"earliest": None, "latest": None},
        }

        total_rounds = 0
        timestamps = []

        for _, info in selected_files:
            # 按游戏类型统计
            game_type = info["game_type"]
            stats["by_game_type"][game_type] = (
                stats["by_game_type"].get(game_type, 0) + 1
            )

            # 按胜利者统计
            winner = info["winner"]
            stats["by_winner"][winner] = stats["by_winner"].get(winner, 0) + 1

            # 按玩家数统计
            player_count = info["player_count"]
            stats["by_player_count"][str(player_count)] = (
                stats["by_player_count"].get(str(player_count), 0) + 1
            )

            # 轮数统计
            total_rounds += info["rounds"]

            # 时间统计
            timestamps.append(info["timestamp"])

        if len(selected_files) > 0:
            stats["average_rounds"] = round(total_rounds / len(selected_files), 1)
            stats["date_range"]["earliest"] = min(timestamps)
            stats["date_range"]["latest"] = max(timestamps)

        # 保存统计文件
        stats_file = self.target_dir / "games_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"Statistics saved to {stats_file}")
        return stats

    def organize(self):
        """执行完整的整理流程"""
        print("Starting game log organization...")

        # 清理目标目录
        if self.target_dir.exists():
            shutil.rmtree(self.target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)

        # 清理reviews目标目录
        if self.reviews_target_dir.exists():
            shutil.rmtree(self.reviews_target_dir)
        self.reviews_target_dir.mkdir(parents=True, exist_ok=True)
        self.target_dir.mkdir(parents=True, exist_ok=True)

        # 过滤和选择文件
        selected_files = self.filter_logs()

        if not selected_files:
            print("No suitable game logs found")
            return 0

        # 复制文件
        count = self.copy_selected_logs(selected_files)

        # 创建统计
        stats = self.create_summary_stats(selected_files)

        print(f"\n=== Organization Complete ===")
        print(f"Total files: {count}")
        print(f"Game types: {list(stats['by_game_type'].keys())}")
        print(f"Average rounds: {stats['average_rounds']}")

        return count


def main():
    organizer = GameLogOrganizer()
    count = organizer.organize()

    # 为GitHub Actions输出
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"count={count}\n")


if __name__ == "__main__":
    main()
