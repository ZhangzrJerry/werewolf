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

````python
from werewolf import WerewolfGame

# 创建一个6人局游戏
players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
# Werewolf Game

一个使用 AgentScope 实现的可迭代多智能体狼人杀游戏，支持规则引擎与 LLM 智能对局两种模式。

## 🚀 快速开始（Windows PowerShell）

```powershell
# 1) 激活虚拟环境
.\env\Scripts\Activate.ps1

# 2) 安装项目
pip install -e .

# 3) 可选：安装测试依赖
pip install -e ".[test]"
````

### 启动方式 A：规则演示（无需模型/AgentScope）

最简单的演示，使用固定策略展示回合流程：

```powershell
python demo_simple.py
```

### 启动方式 B：多智能体对局（需要 AgentScope + 模型）

> ⚠️ **当前状态**：完整的 AgentScope 编排器 (`run_game.py`) 需要进一步配置适配。  
> 推荐先使用 **启动方式 A** 或查看 `GUIDE.md` 了解完整功能。

1. 安装 AgentScope：

```powershell
pip install agentscope
```

2. 编辑 `werewolf/config.py`，选择模型并设置 API Key：

- DashScope（通义千问）示例：`DEFAULT_MODEL = "dashscope_chat"`，填写 `api_key`
- OpenAI 示例：`DEFAULT_MODEL = "openai_chat"`，填写 `api_key`
- 本地 Ollama：`DEFAULT_MODEL = "ollama_chat"`，确保本机已启动 Ollama 服务

3. 尝试简化演示（包含 AgentScope 初始化）：

```powershell
python demo_agentscope.py
```

或参考 `GUIDE.md` 中的详细配置和自定义编排方案。

## 🧩 仅用规则引擎（编程接口）

```python
from werewolf import WerewolfGame

players = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
game = WerewolfGame(players, game_type="six")

state = game.to_dict()
print(state)
```

## 🧪 运行测试

```powershell
# 使用 unittest
python -m unittest discover tests -v

# 或使用测试脚本
python run_tests.py

# 或使用 pytest（需先安装）
pytest -q
```

更详细的测试说明见 `tests/README.md`，整体测试总结见 `TESTING.md`。

## 📁 项目结构

```
werewolf/
├── werewolf/
│   ├── __init__.py           # 包导出
│   ├── WerewolfGame.py       # 规则与状态机（不依赖 LLM）
│   ├── agents.py             # 智能体实现（对 AgentScope 软依赖，测试环境可用 stub）
│   ├── orchestrator.py       # 多智能体编排器（讨论/投票/夜间行动）
│   └── config.py             # 模型与游戏配置（默认模型、API Key）
├── tests/
│   ├── test_werewolf_game.py # 规则单测
│   └── test_agents.py        # 智能体单测（mock/stub，不触发真实调用）
├── demo_simple.py            # 规则演示脚本（无需模型/AgentScope）
├── run_game.py               # 多智能体对局入口（需 AgentScope + 模型）
├── GUIDE.md                  # 玩法、配置与扩展指南
├── TESTING.md                # 测试覆盖与说明
├── pyproject.toml            # 项目配置
└── README.md                 # 本文件
```

## ✨ 功能特性

- 支持 6/9/12 人局角色配置
- 角色：狼人、村民、预言家、女巫、猎人、守卫
- 夜/昼阶段完整规则与胜负判定
- 智能体具备角色化提示、记忆、讨论与投票能力
- 兼容无 AgentScope 的测试/演示环境

## 🔧 常见问题（Troubleshooting）

详细的故障排除指南请查看 [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)

快速解决方案：

- **ImportError: agentscope**：`pip install agentscope` 或使用 `demo_simple.py`
- **API Key 错误**：在 `werewolf/config.py` 填写正确的 Key
- **运行缓慢**：减少 `discussion_rounds` 或使用更快的模型（如 `qwen-turbo`）
- **测试失败**：确保 Python 3.10+ 且已运行 `pip install -e ".[test]"`
