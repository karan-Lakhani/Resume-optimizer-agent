# config/settings.py

import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

# 1. Find the project's root folder and load .env from there
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

class Settings:
    # 2. Read each value, with a fallback default if missing
    llm_provider: str = os.getenv("LLM_PROVIDER")
    llm_model: str = os.getenv("LLM_MODEL")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")

    jsearch_api_key: str | None = os.getenv("JSEARCH_API_KEY")

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/career_agent.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

# 3. A function so the rest of the app can get one shared Settings object
@lru_cache
def get_settings() -> Settings:
    return Settings()