"""
Configuration file for Werewolf Multi-Agent Game
"""

import os
from pathlib import Path

# Load environment variables from .env.local if it exists
try:
    from dotenv import load_dotenv

    env_file = Path(__file__).parent.parent / ".env.local"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not installed, fall back to system env vars

# Model configurations for AgentScope
MODEL_CONFIGS = [
    {
        "config_name": "dashscope_chat",
        "model_type": "dashscope_chat",
        "model_name": "qwen-plus",  # or qwen-turbo, qwen-max
        # Prefer environment variable to avoid hardcoding secrets
        "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
        "generate_args": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    },
    {
        "config_name": "openai_chat",
        "model_type": "openai_chat",
        "model_name": "gpt-4o-mini",  # light & cost-effective; adjust as needed
        # Read from env; set $env:OPENAI_API_KEY before running
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "organization": os.getenv("OPENAI_ORG", ""),  # Optional
        "generate_args": {
            "temperature": 0.7,
            "max_tokens": 500,
        },
    },
    {
        "config_name": "ollama_chat",
        "model_type": "ollama_chat",
        "model_name": "llama2",  # or qwen, mistral, etc.
        "host": "http://localhost:11434",
        "generate_args": {
            "temperature": 0.7,
        },
    },
    {
        "config_name": "deepseek_chat",
        "model_type": "openai_chat",  # DeepSeek uses OpenAI-compatible API
        "model_name": "deepseek-chat",  # or deepseek-coder
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": "https://api.deepseek.com",  # DeepSeek endpoint
        "generate_args": {
            "temperature": 0.7,
            "max_tokens": 500,
            "stream": True,  # Enable streaming to avoid stream_options error
        },
    },
    {
        "config_name": "modelscope_chat",
        "model_type": "openai_chat",  # ModelScope API-Inference uses OpenAI-compatible API
        "model_name": "Qwen/Qwen2.5-72B-Instruct",  # ModelScope Model-Id
        "api_key": os.getenv("MODELSCOPE_API_KEY", ""),
        "base_url": "https://api-inference.modelscope.cn/v1",  # ModelScope API endpoint
        "generate_args": {
            "temperature": 0.7,
            "max_tokens": 500,
            "stream": True,  # Use streaming (AgentScope bug with stream_options when stream=False)
        },
    },
]

# Game configurations
GAME_CONFIG = {
    "game_type": "six",  # six, nine, or twelve
    "max_rounds": 20,
    "discussion_rounds": 3,  # Number of discussion rounds per day
    "verbose": True,
}

# Player names (can be customized)
PLAYER_NAMES_6 = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
PLAYER_NAMES_9 = [
    "Alice",
    "Bob",
    "Charlie",
    "David",
    "Eve",
    "Frank",
    "Grace",
    "Henry",
    "Iris",
]
PLAYER_NAMES_12 = [
    "Alice",
    "Bob",
    "Charlie",
    "David",
    "Eve",
    "Frank",
    "Grace",
    "Henry",
    "Iris",
    "Jack",
    "Kate",
    "Leo",
]

# Select model to use (change this to switch models)
DEFAULT_MODEL = "dashscope_chat"  # or "openai_chat", "ollama_chat"


def get_available_model() -> str:
    """
    Auto-detect and return the first available model based on API key configuration.
    Falls back to DEFAULT_MODEL if none found.

    Priority order: modelscope -> deepseek -> openai -> dashscope -> ollama
    """
    # Priority: free/accessible options first
    if os.getenv("MODELSCOPE_API_KEY"):
        return "modelscope_chat"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek_chat"
    if os.getenv("OPENAI_API_KEY"):
        return "openai_chat"
    if os.getenv("DASHSCOPE_API_KEY"):
        return "dashscope_chat"

    # Ollama doesn't need API key, but check if service is reachable
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            return "ollama_chat"
    except Exception:
        pass

    # Fallback to default
    return DEFAULT_MODEL


# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "save_to_file": True,
    "log_file": "werewolf_game.log",
}
