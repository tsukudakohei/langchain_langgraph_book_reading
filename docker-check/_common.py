from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


DEFAULT_OPENAI_MODEL = "gpt-5-mini"


def is_dry_run() -> bool:
    return os.getenv("DRY_RUN") == "1"


def get_openai_model() -> str:
    model = os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
    # Allow either "gpt-5-mini" or "openai:gpt-5-mini".
    if ":" in model:
        _, model = model.split(":", 1)
    return model


def get_langchain_model_handle() -> str:
    """Return a model handle suitable for LangChain's init_chat_model/create_agent.

    Examples:
      - OPENAI_MODEL="gpt-5-mini"        -> "openai:gpt-5-mini"
      - OPENAI_MODEL="openai:gpt-5-mini" -> "openai:gpt-5-mini"
    """
    return f"openai:{get_openai_model()}"


def ensure_openai_api_key() -> bool:
    if os.getenv("OPENAI_API_KEY"):
        return True
    print(
        "OPENAI_API_KEY が未設定です。.env を作成して設定してください。\n"
        "例: cp .env.example .env"
    )
    return False
