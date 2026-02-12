from __future__ import annotations

import sys
from datetime import datetime, timezone

from _common import ensure_openai_api_key, get_openai_model, is_dry_run


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは OpenAI Agents SDK（Runner / function_tool）の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from agents import Agent, ModelSettings, Runner, function_tool

    @function_tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    @function_tool
    def now_utc() -> str:
        """Return the current UTC time in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    agent = Agent(
        name="demo-agent",
        model=get_openai_model(),
        model_settings=ModelSettings(temperature=0),
        tools=[add, now_utc],
        instructions=(
            "You are a helpful assistant.\n"
            "You MUST use tools.\n"
            "1) Call add(a=3, b=5).\n"
            "2) Call now_utc().\n"
            "3) Finally, answer in Japanese in ONE concise sentence.\n"
        ),
    )

    result = Runner.run_sync(
        agent,
        "次の2つをしてください: 1) 3+5 を計算 2) 現在のUTC時刻を取得。最後に日本語で1文にまとめて答えてください。",
    )
    print(result.final_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())

