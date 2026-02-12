from __future__ import annotations

import sys

from _common import ensure_openai_api_key, get_langchain_model_handle, is_dry_run


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは Structured Output（response_format）の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from pydantic import BaseModel, Field

    from langchain.agents import create_agent
    from langchain.agents.structured_output import ToolStrategy

    class ContactInfo(BaseModel):
        """Extracted contact info."""

        name: str = Field(..., description="Person name")
        email: str | None = Field(None, description="Email address if present")
        phone: str | None = Field(None, description="Phone number if present")

    text = (
        "Hello! My name is Yuki. "
        "You can reach me at yuki@example.com or +1-555-0100."
    )

    # ToolStrategy: モデルのネイティブstructured output対応に依存せず動きやすい。
    agent_tool = create_agent(
        model=get_langchain_model_handle(),
        tools=[],
        response_format=ToolStrategy(ContactInfo),
        system_prompt="Extract contact info from the user's text.",
    )
    out_tool = agent_tool.invoke({"messages": [("user", text)]})

    print("=== ToolStrategy ===")
    structured = out_tool.get("structured_response")
    print(structured)
    if structured is not None and hasattr(structured, "model_dump"):
        print(structured.model_dump())

    # ProviderStrategy (auto): 対応モデルならネイティブstructured outputを優先。
    agent_auto = create_agent(
        model=get_langchain_model_handle(),
        tools=[],
        response_format=ContactInfo,
        system_prompt="Extract contact info from the user's text.",
    )
    out_auto = agent_auto.invoke({"messages": [("user", text)]})

    print("\n=== ProviderStrategy (auto) ===")
    structured2 = out_auto.get("structured_response")
    print(structured2)
    if structured2 is not None and hasattr(structured2, "model_dump"):
        print(structured2.model_dump())

    return 0


if __name__ == "__main__":
    sys.exit(main())
