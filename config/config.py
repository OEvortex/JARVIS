import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # File Paths
    HISTORY_FOLDER: str = "History"
    if not os.path.exists(HISTORY_FOLDER):
        os.makedirs(HISTORY_FOLDER)
    DATASET_FILE: str = os.path.join(HISTORY_FOLDER, "tool_usage.json")

    MEMORY_FILE: str = os.path.join(HISTORY_FOLDER, "memory.txt")
    CHAT_HISTORY_FILE: str = os.path.join(HISTORY_FOLDER, "chat.txt")
    CONVERSATION_HISTORY_FILE: str = os.path.join(HISTORY_FOLDER, "JARVISConversation_history.txt")

    # Conversation Settings
    MAX_TOKENS: int = 8000
    HISTORY_OFFSET: int = 10250
    PROMPT_ALLOWANCE: int = 10
    SAVE_INTERVAL: int = 300  # 5 minutes in seconds

    # User Settings
    DEFAULT_USER: str = "Vortex"
