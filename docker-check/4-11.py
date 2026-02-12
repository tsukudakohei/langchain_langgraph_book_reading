from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from _common import ensure_openai_api_key, get_openai_model, is_dry_run


def _short_json(obj: Any, max_len: int = 220) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)
    if len(s) <= max_len:
        return s
    return s[: max_len - 16] + "...(truncated)"


def _summarize_input_item(item: Any) -> str:
    if isinstance(item, str):
        return f"<str> {item}"
    if isinstance(item, dict):
        if "role" in item and "content" in item:
            return f"{item.get('role')}: {item.get('content')}"
        if "type" in item:
            t = item.get("type")
            if t == "function_call_output":
                return f"type=function_call_output call_id={item.get('call_id')} output={_short_json(item.get('output'))}"
            return f"type={t} {_short_json(item)}"
        return _short_json(item)
    return f"<{type(item).__name__}> {item!r}"


def _print_items(title: str, items: list[Any], tail: int = 8) -> None:
    print(title)
    print(f"count={len(items)}")
    if not items:
        return
    start = max(0, len(items) - tail)
    for i in range(start, len(items)):
        print(f"[{i}] {_summarize_input_item(items[i])}")


def _extract_text_delta(raw_event: Any) -> str:
    # OpenAI Responses streaming events include e.g.:
    # type="response.output_text.delta", delta="..."
    typ = getattr(raw_event, "type", "")
    if typ == "response.output_text.delta":
        return getattr(raw_event, "delta", "") or ""
    return ""


def _summarize_run_item(name: str, item: Any) -> str:
    from agents.items import (  # local import to keep DRY_RUN fast
        HandoffCallItem,
        HandoffOutputItem,
        ItemHelpers,
        MCPApprovalRequestItem,
        MCPApprovalResponseItem,
        MCPListToolsItem,
        MessageOutputItem,
        ReasoningItem,
        ToolApprovalItem,
        ToolCallItem,
        ToolCallOutputItem,
    )

    prefix = f"[run_item] {name}:"

    if isinstance(item, ToolCallItem):
        raw = item.raw_item
        tool_name = getattr(raw, "name", None)
        args = getattr(raw, "arguments", None)
        call_id = getattr(raw, "call_id", None)
        return f"{prefix} tool={tool_name} call_id={call_id} args={args}"

    if isinstance(item, ToolCallOutputItem):
        raw = item.raw_item
        call_id = getattr(raw, "call_id", None) if hasattr(raw, "call_id") else None
        return f"{prefix} call_id={call_id} output={_short_json(item.output)}"

    if isinstance(item, MessageOutputItem):
        text = ItemHelpers.text_message_output(item).strip()
        if len(text) > 120:
            text = text[:100] + "...(truncated)"
        return f"{prefix} text={text}"

    if isinstance(item, ReasoningItem):
        return f"{prefix} <reasoning_item>"

    if isinstance(item, HandoffCallItem):
        raw = item.raw_item
        return f"{prefix} <handoff_call> name={getattr(raw, 'name', None)}"

    if isinstance(item, HandoffOutputItem):
        return f"{prefix} <handoff_output> source={getattr(item.source_agent, 'name', None)} target={getattr(item.target_agent, 'name', None)}"

    if isinstance(item, MCPListToolsItem):
        return f"{prefix} <mcp_list_tools>"

    if isinstance(item, MCPApprovalRequestItem):
        return f"{prefix} <mcp_approval_requested>"

    if isinstance(item, MCPApprovalResponseItem):
        return f"{prefix} <mcp_approval_response>"

    if isinstance(item, ToolApprovalItem):
        return f"{prefix} <tool_approval_requested> tool_name={item.tool_name}"

    return f"{prefix} {_short_json(getattr(item, '__dict__', str(item)))}"


async def _run() -> int:
    from agents import Agent, ModelSettings, Runner, function_tool

    @function_tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    agent = Agent(
        name="stream-agent",
        model=get_openai_model(),
        model_settings=ModelSettings(temperature=0),
        tools=[add],
        instructions=(
            "You are a helpful assistant.\n"
            "You MUST use the add tool at least once.\n"
            "First, compute 12+34 by calling add(a=12, b=34).\n"
            "Then, write a short Japanese story (~200 chars) that includes the computed number.\n"
        ),
    )

    prompt = "短い物語を作ってください。"
    input_items = [{"role": "user", "content": prompt}]
    initial_count = len(input_items)

    _print_items("=== initial input items ===", input_items, tail=20)

    print("\n=== stream (raw delta) ===")
    stream = Runner.run_streamed(agent, input_items)

    event_log: list[str] = []

    async for event in stream.stream_events():
        if event.type == "raw_response_event":
            delta = _extract_text_delta(event.data)
            if delta:
                print(delta, end="", flush=True)
        elif event.type == "run_item_stream_event":
            event_log.append(_summarize_run_item(event.name, event.item))
        elif event.type == "agent_updated_stream_event":
            event_log.append(f"[agent_updated] new_agent={event.new_agent.name}")

    print("\n")

    print("=== event log (run_item_stream_event) ===")
    for line in event_log:
        print(line)

    print("\n=== final_output ===")
    print(stream.final_output)

    items = stream.to_input_list()
    _print_items("\n=== to_input_list() tail (merged input + new items) ===", items)
    print(f"\n(input items grew: {initial_count} -> {len(items)})")
    return 0


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは streaming events（raw delta + run_item_stream_event）の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
