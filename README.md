# Werewolf Game

一个使用 AgentScope 实现的多智能体狼人杀游戏。

## 安装

```powershell
# 激活虚拟环境
.\env\Scripts\Activate.ps1

# 安装项目
pip install -e .

# 安装测试依赖（可选）
pip install -e ".[test]"
```

## 使用方法

```python
from werewolf import WerewolfGame

# 创建一个6人局游戏
players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
game = WerewolfGame(players, game_type="six")

# 查看游戏状态
state = game.to_dict()
print(state)
```

## 运行测试

```powershell
# 使用 unittest
python -m unittest discover tests -v

# 或使用测试脚本
python run_tests.py

# 使用 pytest（需要先安装）
pytest
```

详细的测试文档请查看 [tests/README.md](tests/README.md)

## 项目结构

```
werewolf/
├── werewolf/           # 主包
│   ├── __init__.py
│   └── WerewolfGame.py # 游戏核心逻辑
├── tests/              # 测试文件
│   ├── __init__.py
│   ├── test_werewolf_game.py
│   └── README.md       # 测试文档
├── pyproject.toml      # 项目配置
├── run_tests.py        # 测试运行脚本
└── README.md           # 本文件
```

## 功能特性

- 支持 6 人局、9 人局、12 人局等不同配置
- 实现了经典角色：狼人、村民、预言家、女巫、猎人、守卫
- 完整的夜晚和白天阶段逻辑
- 女巫毒药和解药机制
- 守卫保护机制（不能连续两晚保护同一玩家）
- 特殊规则：守卫和女巫同时救人时目标仍然死亡
- 完善的游戏结束判定

## 测试覆盖

项目包含 23 个单元测试，覆盖：

- ✅ 游戏初始化
- ✅ 角色分配
- ✅ 夜晚阶段（狼人、预言家、女巫）
- ✅ 守卫功能
- ✅ 白天投票
- ✅ 游戏结束条件
- ✅ 游戏状态管理

## 开发

```powershell
# 克隆仓库后
.\env\Scripts\Activate.ps1

# 安装开发依赖
pip install -e ".[test]"

# 运行测试
python run_tests.py
```
