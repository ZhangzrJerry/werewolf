"""
自我对弈训练示例

演示如何使用 run_selfplay.py 进行策略迭代训练
"""

# 示例 1: 快速开始 - 运行 10 局游戏
# python run_selfplay.py -n 10

# 示例 2: 并行训练 - 使用 4 个进程同时运行
# python run_selfplay.py -n 50 -p 4

# 示例 3: 9 人局训练
# python run_selfplay.py -n 30 -t nine

# 示例 4: 从头开始训练（清除之前的进度）
# python run_selfplay.py -n 20 --no-resume

# 示例 5: 详细输出模式
# python run_selfplay.py -n 5 -v

# 示例 6: 大规模训练 - 100 局并行
# python run_selfplay.py -n 100 -p 8

# 中断和恢复：
# 1. 运行训练: python run_selfplay.py -n 100 -p 4
# 2. 按 Ctrl+C 中断
# 3. 再次运行相同命令，会自动从中断处继续

# 查看训练进度：
# python -c "import json; print(json.dumps(json.load(open('training_progress/progress.json')), indent=2, ensure_ascii=False))"

# 查看策略文件：
# Get-Content strategies/werewolf.json
# Get-Content strategies/seer.json
# Get-Content strategies/villager.json
# Get-Content strategies/witch.json
# Get-Content strategies/guardian.json
# Get-Content strategies/hunter.json

print(
    """
狼人杀自我对弈训练指南
====================

基础用法：
---------
python run_selfplay.py -n <游戏数> [-p <并行数>] [-t <游戏类型>]

参数说明：
---------
-n, --num-games    要运行的游戏局数 (默认: 50)
-p, --parallel     并行进程数 (默认: 1, 最大: 8)
-t, --type         游戏类型: six/nine/twelve (默认: six)
-v, --verbose      显示详细游戏过程
--no-resume        从头开始，忽略之前的训练进度

推荐配置：
---------
- 快速测试:       python run_selfplay.py -n 10
- 标准训练:       python run_selfplay.py -n 50 -p 4
- 深度训练:       python run_selfplay.py -n 200 -p 8
- 9人局训练:      python run_selfplay.py -n 100 -t nine -p 4

训练数据位置：
-----------
- 策略文件:       strategies/
  - 当前策略:     strategies/*.json
  - 历史备份:     strategies/backups/*_YYYYMMDD_HHMMSS.json
- 游戏日志:       game_logs/
- 复盘分析:       reviews/
- 训练进度:       training_progress/progress.json

提示：
-----
1. 训练可以随时中断 (Ctrl+C)，下次运行会自动继续
2. 策略会在每局游戏后自动更新
3. 每次更新策略前会自动备份旧版本到 strategies/backups/
4. 使用 -p 参数可以显著加速训练（推荐 4-8 个进程）
5. 查看 training_progress/progress.json 了解详细训练统计

策略版本管理：
-----------
- 当前策略:    strategies/werewolf.json
- 历史版本:    strategies/backups/werewolf_20251026_120000.json
- 恢复旧版本:  Copy-Item strategies/backups/werewolf_20251026_120000.json strategies/werewolf.json
"""
)
