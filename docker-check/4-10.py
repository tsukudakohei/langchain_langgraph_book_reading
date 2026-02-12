from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from _common import ensure_openai_api_key, get_openai_model, is_dry_run


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは Agents SDK Sessions（SQLiteSession）の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from agents import Agent, ModelSettings, Runner, SQLiteSession

    db_path = Path(__file__).with_name("agents_sdk_conversations.db")

    session1 = SQLiteSession("demo-session", db_path=db_path)
    session2 = SQLiteSession("other-session", db_path=db_path)

    # Re-run friendly: clear sessions so the demo output doesn't depend on past runs.
    asyncio.run(session1.clear_session())
    asyncio.run(session2.clear_session())

    agent = Agent(
        name="session-agent",
        model=get_openai_model(),
        model_settings=ModelSettings(temperature=0),
        instructions="You are a helpful assistant. Answer in Japanese. Keep responses short.",
    )

    print("db_path:", db_path)

    print("\n=== turn 1 (demo-session) ===")
    out1 = Runner.run_sync(agent, "私の名前は太郎です。覚えてください。", session=session1)
    print(out1.final_output)

    print("\n=== turn 2 (same session_id) ===")
    out2 = Runner.run_sync(agent, "私の名前は何でしたか？", session=session1)
    print(out2.final_output)

    print("\n=== turn 3 (different session_id) ===")
    out3 = Runner.run_sync(agent, "私の名前は何でしたか？（新しいセッション）", session=session2)
    print(out3.final_output)

    session1.close()
    session2.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

