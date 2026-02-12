from __future__ import annotations

import sys

from _common import ensure_openai_api_key, get_langchain_model_handle, is_dry_run


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは LangChain Tools（@tool / ToolRuntime / Command）の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from typing import NotRequired

    from langchain.agents import AgentState, create_agent
    from langchain.tools import tool
    from langchain.tools import ToolRuntime
    from langgraph.types import Command

    # 1) @tool の最小例（ツール単体で呼ぶ）
    @tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    print("=== tool.invoke ===")
    print(add.invoke({"a": 2, "b": 3}))

    # 2) runtime.state を読むツール
    @tool
    def show_user_name(runtime: ToolRuntime[None, StateSchema]) -> str:
        """Read user_name from the graph/agent state."""
        user_name = runtime.state.get("user_name", "<unset>")
        return f"user_name={user_name}"

    # 3) Command(update=...) で state を更新するツール
    @tool
    def set_user_name(name: str) -> Command:
        """Set user_name in the state."""
        return Command(update={"user_name": name})

    class StateSchema(AgentState):
        user_name: NotRequired[str]

    agent = create_agent(
        model=get_langchain_model_handle(),
        tools=[add, set_user_name, show_user_name],
        state_schema=StateSchema,
        system_prompt=(
            "You must use tools.\n"
            "First call set_user_name with name='Alice'.\n"
            "Then call show_user_name.\n"
            "Finally, greet the user in Japanese in one short sentence."
        ),
    )

    result = agent.invoke({"messages": [("user", "ツールを使って user_name を設定して確認して。")]})
    print("\n=== state ===")
    print("user_name:", result.get("user_name"))

    print("\n=== final message ===")
    messages = result.get("messages", [])
    last = messages[-1] if messages else None
    content = getattr(last, "content", str(last))
    print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
