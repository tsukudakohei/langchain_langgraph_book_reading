from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import env_bool, load_dotenv_if_present, print_section, require_env, warn  # type: ignore


def main() -> None:
    load_dotenv_if_present()

    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="LangChain Runnable とは？")
    ap.add_argument("--openai-model", default=os.getenv("OPENAI_SEARCH_MODEL", "gpt-5"))
    ap.add_argument("--tavily-depth", default=os.getenv("TAVILY_SEARCH_DEPTH", "basic"), choices=["basic", "advanced"])
    args = ap.parse_args()

    dry_run = env_bool("DRY_RUN", False)
    if dry_run:
        print_section(
            "DRY_RUN",
            f"""
            DRY_RUN=1 のため、実際のWeb検索は行いません。
            - OpenAI Responses API web search と Tavily の比較用“雛形”です。
            query: {args.query}
            """,
        )
        return

    print_section("query", args.query)

    # 1) OpenAI Responses API built-in web search tool
    if require_env("OPENAI_API_KEY"):
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI()
            resp = client.responses.create(
                model=args.openai_model,
                input=args.query,
                tools=[{"type": "web_search"}],
            )
            # まずはテキストだけ表示（詳細は必要に応じて include などで拡張）
            print_section("OpenAI web_search (Responses API)", resp.output_text)
        except Exception as e:
            warn(f"OpenAI web_search failed: {e}")
    else:
        warn("OPENAI_API_KEY が無いので OpenAI web_search はスキップします。")

    # 2) Tavily Search API
    if require_env("TAVILY_API_KEY"):
        try:
            from tavily import TavilyClient  # type: ignore

            tv = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            result = tv.search(query=args.query, search_depth=args.tavily_depth, max_results=5)
            # 必要最低限だけ表示
            items = result.get("results", [])
            lines = []
            for i, it in enumerate(items, 1):
                lines.append(f"[{i}] {it.get('title')}\n  url: {it.get('url')}\n  score: {it.get('score')}\n  content: {str(it.get('content'))[:240]}")
            print_section("Tavily search", "\n\n".join(lines) if lines else "(no results)")
        except Exception as e:
            warn(f"Tavily search failed: {e}")
    else:
        warn("TAVILY_API_KEY が無いので Tavily はスキップします。")


if __name__ == "__main__":
    main()
