from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

# docker-check/ 直下の _common.py を import するためにパスを調整
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import env_bool, load_dotenv_if_present, print_section  # type: ignore


def _pkg_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "(not installed)"


def main() -> None:
    load_dotenv_if_present()

    pkgs = [
        "openai",
        "langchain",
        "langchain-core",
        "langchain-openai",
        "langchain-community",
        "langchain-text-splitters",
        "langchain-chroma",
        "chromadb",
        "tavily",
    ]

    lines = [f"Python: {sys.version.split()[0]}"]
    lines.append(f"DRY_RUN: {env_bool('DRY_RUN', False)}")
    lines.append("")
    lines.append("Installed packages:")
    for p in pkgs:
        lines.append(f"  - {p}: {_pkg_version(p)}")

    print_section("ch04 smoke check", "\n".join(lines))

    print_section(
        "next steps",
        """
        - 依存が足りない場合:
            pip install -r requirements.txt

        - APIキー無しでRAG疎通:
            DRY_RUN=1 python docker-check/ch04/01_build_vectorstore.py
            DRY_RUN=1 python docker-check/ch04/02_rag_chain_lcel.py --query "このリポジトリの目的は？"
        """,
    )


if __name__ == "__main__":
    main()
