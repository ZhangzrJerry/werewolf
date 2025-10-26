# Werewolf Game - 测试指南

## 安装测试依赖

```bash
pip install -e ".[test]"
```

或者直接安装 pytest：

```bash
pip install pytest pytest-cov
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
pytest tests/test_werewolf_game.py
```

### 运行特定测试类

```bash
pytest tests/test_werewolf_game.py::TestWerewolfGameInit
```

### 运行特定测试方法

```bash
pytest tests/test_werewolf_game.py::TestWerewolfGameInit::test_init_minimum_players
```

### 查看详细输出

```bash
pytest -v
```

### 生成覆盖率报告

```bash
pytest --cov=werewolf --cov-report=html
```

覆盖率报告将生成在 `htmlcov/index.html`

### 运行并查看失败详情

```bash
pytest -vv --tb=long
```

## 测试结构

```
tests/
├── __init__.py
└── test_werewolf_game.py   # WerewolfGame 的单元测试
```

## 测试覆盖范围

单元测试涵盖以下功能：

### 1. 游戏初始化测试 (TestWerewolfGameInit)

- 最少玩家数量验证
- 6 人局初始化
- 9 人局初始化
- 12 人局初始化

### 2. 角色分配测试 (TestRoleAssignment)

- 6 人局角色分配（2 狼人、2 村民、1 预言家、1 女巫）
- 9 人局角色分配（3 狼人、3 村民、1 预言家、1 女巫、1 猎人）
- 12 人局角色分配（4 狼人、4 村民、1 预言家、1 女巫、1 猎人、1 守卫）

### 3. 夜晚阶段测试 (TestNightPhase)

- 狼人击杀
- 预言家查验
- 女巫救人
- 女巫毒杀
- 女巫技能单次使用限制

### 4. 守卫功能测试 (TestGuardian)

- 守卫保护玩家
- 守卫不能连续两晚保护同一玩家
- 守卫和女巫同时救人时的特殊规则（玩家仍然死亡）

### 5. 白天阶段测试 (TestDayPhase)

- 投票淘汰
- 平票时无人淘汰
- 天数计数器增加

### 6. 游戏结束条件测试 (TestGameEndConditions)

- 狼人全灭时好人获胜
- 狼人数量大于等于好人时狼人获胜
- 游戏未结束时继续进行

### 7. 游戏状态测试 (TestGameState)

- 状态转字典
- 游戏日志记录

## 使用 unittest 运行

如果你更喜欢使用 unittest：

```bash
python -m unittest discover tests
```

或者直接运行测试文件：

```bash
python tests/test_werewolf_game.py
```
