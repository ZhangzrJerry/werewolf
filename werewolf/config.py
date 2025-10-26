"""
Configuration file for Werewolf Multi-Agent Game
"""

# Model configurations for AgentScope
MODEL_CONFIGS = [
    {
        "config_name": "dashscope_chat",
        "model_type": "dashscope_chat",
        "model_name": "qwen-plus",  # or qwen-turbo, qwen-max
        "api_key": "YOUR_DASHSCOPE_API_KEY",  # Replace with your API key
        "generate_args": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    },
    {
        "config_name": "openai_chat",
        "model_type": "openai_chat",
        "model_name": "gpt-4",  # or gpt-3.5-turbo
        "api_key": "YOUR_OPENAI_API_KEY",  # Replace with your API key
        "organization": "YOUR_ORG_ID",  # Optional
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

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "save_to_file": True,
    "log_file": "werewolf_game.log",
}
