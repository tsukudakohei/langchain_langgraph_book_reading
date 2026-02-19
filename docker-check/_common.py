from __future__ import annotations

import os
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def load_dotenv_if_present() -> None:
    """Load .env if python-dotenv is installed and .env exists."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv()


def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def require_env(name: str) -> str | None:
    v = os.getenv(name)
    return v if v and v.strip() else None


def project_root_from_docker_check() -> Path:
    """
    docker-check/ 直下にこのファイルがある想定。
    repo ルートは親ディレクトリ。
    """
    return Path(__file__).resolve().parent.parent


def default_chroma_dir(chapter: str) -> Path:
    return project_root_from_docker_check() / ".chroma" / chapter


def print_section(title: str, body: str) -> None:
    print(f"\n=== {title} ===")
    print(textwrap.dedent(body).strip())


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"[INFO] {msg}")
