from __future__ import annotations

import sys

from _common import ensure_openai_api_key, get_langchain_model_handle, is_dry_run


def _last_ai_content(state: dict) -> str:
    messages = state.get("messages", [])
    last = messages[-1] if messages else None
    return getattr(last, "content", str(last))


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは Short-term-memory（checkpointer + thread_id）の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import InMemorySaver

    checkpointer = InMemorySaver()
    agent = create_agent(
        model=get_langchain_model_handle(),
        tools=[],
        checkpointer=checkpointer,
        system_prompt="You are a helpful assistant. Answer in Japanese.",
    )

    cfg = {"configurable": {"thread_id": "demo-thread"}}

    print("=== turn 1 ===")
    out1 = agent.invoke({"messages": [("user", "私の名前は太郎です。覚えてください。")]}, cfg)
    print(_last_ai_content(out1))

    print("\n=== turn 2 (same thread_id) ===")
    out2 = agent.invoke({"messages": [("user", "私の名前は何でしたか？")]}, cfg)
    print(_last_ai_content(out2))

    print("\n=== turn 3 (different thread_id) ===")
    out3 = agent.invoke(
        {"messages": [("user", "私の名前は何でしたか？（新しいスレッド）")]},
        {"configurable": {"thread_id": "other-thread"}},
    )
    print(_last_ai_content(out3))

    return 0


if __name__ == "__main__":
    sys.exit(main())

