from __future__ import annotations

import sys
from datetime import datetime, timezone

from _common import ensure_openai_api_key, get_langchain_model_handle, is_dry_run


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは LangChain Agents（create_agent）の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from langchain.agents import create_agent
    from langchain.tools import tool

    @tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    @tool
    def now_utc() -> str:
        """Return the current UTC time in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    agent = create_agent(
        model=get_langchain_model_handle(),
        tools=[add, now_utc],
        system_prompt=(
            "You are a helpful assistant. "
            "Use tools when needed. Keep the final answer concise."
        ),
    )

    result = agent.invoke(
        {
            "messages": [
                (
                    "user",
                    "次の2つをしてください: "
                    "1) 3+5 を計算 2) 現在のUTC時刻を取得。"
                    "最後に日本語で1文にまとめて答えてください。",
                )
            ]
        }
    )
    messages = result.get("messages", [])
    last = messages[-1] if messages else None
    content = getattr(last, "content", str(last))
    print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())

