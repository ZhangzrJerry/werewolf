"""
分析狼人杀游戏日志，统计游戏轮次信息并绘制趋势图
跳过因网络中断而未完成的游戏
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime

# 设置中文字体
matplotlib.rcParams["font.sans-serif"] = [
    "SimHei",
    "Microsoft YaHei",
    "Arial Unicode MS",
]
matplotlib.rcParams["axes.unicode_minus"] = False


def is_game_complete(file_path: str) -> bool:
    """
    检查游戏是否完整结束
    完整的游戏应该包含 "GAME OVER" 标记
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            return "GAME OVER" in content
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return False


def extract_game_info(file_path: str) -> Dict:
    """
    从游戏日志中提取关键信息
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取游戏类型
        game_type_match = re.search(r"Game Type:\s*(\w+)", content)
        game_type = game_type_match.group(1) if game_type_match else "unknown"

        # 提取玩家列表
        players_match = re.search(r"Players:\s*(.+)", content)
        players = players_match.group(1) if players_match else ""
        player_count = len(players.split(",")) if players else 0

        # 统计轮次数 - 查找所有 "ROUND X" 标记
        rounds = re.findall(r"ROUND\s+(\d+)", content)
        max_round = max([int(r) for r in rounds]) if rounds else 0

        # 提取获胜方
        winner_match = re.search(r"\[WINNER\]\s*(\w+)", content)
        winner = winner_match.group(1) if winner_match else "unknown"

        # 提取狼人队伍
        werewolf_team_match = re.search(r"Werewolf team:\s*(.+)", content)
        werewolf_team = werewolf_team_match.group(1) if werewolf_team_match else ""

        # 从文件名提取时间戳
        filename = os.path.basename(file_path)
        timestamp_match = re.search(r"werewolf_game_(\d{8}_\d{6})", filename)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        else:
            timestamp = None

        return {
            "file_name": os.path.basename(file_path),
            "timestamp": timestamp,
            "game_type": game_type,
            "player_count": player_count,
            "rounds": max_round,
            "winner": winner,
            "is_complete": True,
            "werewolf_count": len(werewolf_team.split(",")) if werewolf_team else 0,
        }
    except Exception as e:
        print(f"分析文件 {file_path} 时出错: {e}")
        return None


def analyze_game_logs(logs_dir: str) -> Tuple[List[Dict], List[str]]:
    """
    分析所有游戏日志
    返回完整游戏信息和未完成游戏列表
    """
    logs_path = Path(logs_dir)

    if not logs_path.exists():
        print(f"目录不存在: {logs_dir}")
        return [], []

    complete_games = []
    incomplete_games = []

    # 遍历所有 .txt 文件
    for log_file in sorted(logs_path.glob("*.txt")):
        file_path = str(log_file)

        # 检查游戏是否完整
        if is_game_complete(file_path):
            game_info = extract_game_info(file_path)
            if game_info and game_info["timestamp"]:
                complete_games.append(game_info)
        else:
            incomplete_games.append(log_file.name)

    # 按时间排序
    complete_games.sort(key=lambda x: x["timestamp"])

    return complete_games, incomplete_games


def print_statistics(complete_games: List[Dict], incomplete_games: List[str]):
    """
    打印统计信息
    """
    print("=" * 80)
    print("狼人杀游戏日志统计报告")
    print("=" * 80)
    print()

    # 基本统计
    total_games = len(complete_games) + len(incomplete_games)
    print(f"总游戏数: {total_games}")
    print(f"  完整游戏: {len(complete_games)}")
    print(f"  未完成游戏（网络中断等）: {len(incomplete_games)}")
    print()

    if not complete_games:
        print("没有找到完整的游戏记录。")
        return

    # 轮次统计
    print("-" * 80)
    print("轮次统计（仅完整游戏）")
    print("-" * 80)

    round_counts = defaultdict(int)
    for game in complete_games:
        round_counts[game["rounds"]] += 1

    total_rounds = sum(game["rounds"] for game in complete_games)
    avg_rounds = total_rounds / len(complete_games)

    print(f"总轮次数: {total_rounds}")
    print(f"平均轮次: {avg_rounds:.2f}")
    print(f"最短游戏: {min(game['rounds'] for game in complete_games)} 轮")
    print(f"最长游戏: {max(game['rounds'] for game in complete_games)} 轮")
    print()

    print("轮次分布:")
    for rounds in sorted(round_counts.keys()):
        count = round_counts[rounds]
        percentage = (count / len(complete_games)) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {rounds:2d} 轮: {count:4d} 场 ({percentage:5.1f}%) {bar}")
    print()

    # 获胜方统计
    print("-" * 80)
    print("获胜方统计（仅完整游戏）")
    print("-" * 80)

    winner_counts = defaultdict(int)
    for game in complete_games:
        winner_counts[game["winner"]] += 1

    for winner, count in sorted(
        winner_counts.items(), key=lambda x: x[1], reverse=True
    ):
        percentage = (count / len(complete_games)) * 100
        print(f"  {winner:15s}: {count:4d} 场 ({percentage:5.1f}%)")
    print()


def plot_rounds_trend(complete_games: List[Dict], window_size: int = 20):
    """
    绘制平均轮次随迭代次数的变化趋势
    """
    if not complete_games:
        print("没有数据可以绘图")
        return

    # 准备数据
    game_numbers = list(range(1, len(complete_games) + 1))
    rounds = [game["rounds"] for game in complete_games]

    # 计算移动平均
    moving_avg = []
    for i in range(len(rounds)):
        start_idx = max(0, i - window_size + 1)
        window = rounds[start_idx : i + 1]
        moving_avg.append(sum(window) / len(window))

    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # 图1: 每场游戏的轮次 + 移动平均线
    ax1.scatter(
        game_numbers, rounds, alpha=0.3, s=20, label="单场游戏轮次", color="lightblue"
    )
    ax1.plot(
        game_numbers,
        moving_avg,
        color="red",
        linewidth=2,
        label=f"{window_size}场移动平均",
        alpha=0.8,
    )

    # 添加整体平均线
    overall_avg = sum(rounds) / len(rounds)
    ax1.axhline(
        y=overall_avg,
        color="green",
        linestyle="--",
        linewidth=1.5,
        label=f"总体平均 ({overall_avg:.2f}轮)",
        alpha=0.7,
    )

    ax1.set_xlabel("游戏编号（时间顺序）", fontsize=12)
    ax1.set_ylabel("轮次数", fontsize=12)
    ax1.set_title("游戏轮次随迭代次数变化趋势", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, max(rounds) + 1)

    # 图2: 分段统计（每50场游戏的平均轮次）
    segment_size = 50
    segments = []
    segment_labels = []
    segment_avgs = []

    for i in range(0, len(rounds), segment_size):
        segment = rounds[i : i + segment_size]
        if segment:
            segments.append(i // segment_size + 1)
            segment_labels.append(f"{i+1}-{min(i+segment_size, len(rounds))}")
            segment_avgs.append(sum(segment) / len(segment))

    colors = plt.cm.viridis(range(len(segments)))
    bars = ax2.bar(segments, segment_avgs, color=colors, alpha=0.7, edgecolor="black")

    # 在柱状图上标注数值
    for bar, avg in zip(bars, segment_avgs):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{avg:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax2.axhline(
        y=overall_avg,
        color="red",
        linestyle="--",
        linewidth=1.5,
        label=f"总体平均 ({overall_avg:.2f}轮)",
        alpha=0.7,
    )

    ax2.set_xlabel(f"游戏分段（每{segment_size}场）", fontsize=12)
    ax2.set_ylabel("平均轮次数", fontsize=12)
    ax2.set_title(
        f"每{segment_size}场游戏的平均轮次对比", fontsize=14, fontweight="bold"
    )
    ax2.set_xticks(segments)
    ax2.set_xticklabels(segment_labels, rotation=45, ha="right")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    # 保存图表
    output_file = "d:/Projects/werewolf/rounds_trend_analysis.png"
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"\n趋势图已保存到: {output_file}")

    plt.show()

    # 计算趋势分析
    print("\n" + "=" * 80)
    print("趋势分析")
    print("=" * 80)

    # 前1/3 vs 后1/3 对比
    third = len(rounds) // 3
    first_third_avg = sum(rounds[:third]) / third if third > 0 else 0
    last_third_avg = sum(rounds[-third:]) / third if third > 0 else 0
    change = last_third_avg - first_third_avg
    change_pct = (change / first_third_avg * 100) if first_third_avg > 0 else 0

    print(f"前1/3游戏（1-{third}场）平均轮次: {first_third_avg:.2f}")
    print(
        f"后1/3游戏（{len(rounds)-third+1}-{len(rounds)}场）平均轮次: {last_third_avg:.2f}"
    )
    print(f"变化: {change:+.2f} 轮 ({change_pct:+.1f}%)")

    if change > 0.1:
        print("✓ 轮次呈上升趋势")
    elif change < -0.1:
        print("✗ 轮次呈下降趋势")
    else:
        print("→ 轮次基本稳定")


def main():
    # 游戏日志目录
    logs_dir = r"d:\Projects\werewolf\.training\game_logs"

    print("开始分析游戏日志...")
    print()

    # 分析日志
    complete_games, incomplete_games = analyze_game_logs(logs_dir)

    # 打印统计信息
    print_statistics(complete_games, incomplete_games)

    # 绘制趋势图
    if complete_games:
        plot_rounds_trend(complete_games, window_size=20)


if __name__ == "__main__":
    main()
