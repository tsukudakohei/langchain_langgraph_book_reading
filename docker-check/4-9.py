from __future__ import annotations

import json
import sys
from typing import Any

from _common import ensure_openai_api_key, get_openai_model, is_dry_run


def _short_json(obj: Any, max_len: int = 220) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
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


def _print_items(title: str, items: list[Any], tail: int = 6) -> None:
    print(title)
    print(f"count={len(items)}")
    if not items:
        return
    start = max(0, len(items) - tail)
    for i in range(start, len(items)):
        print(f"[{i}] {_summarize_input_item(items[i])}")


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは input items（Responsesの入力items列）+ to_input_list() の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from agents import Agent, ModelSettings, Runner

    agent = Agent(
        name="memory-agent",
        model=get_openai_model(),
        model_settings=ModelSettings(temperature=0),
        instructions="You are a helpful assistant. Answer in Japanese. Keep responses short.",
    )

    print("=== turn 1 ===")
    out1 = Runner.run_sync(agent, "私の名前は太郎です。覚えてください。")
    print("final_output:", out1.final_output)

    items1 = out1.to_input_list()
    _print_items("\n=== to_input_list() after turn 1 (tail) ===", items1)

    items2 = items1 + [{"role": "user", "content": "私の名前は何でしたか？"}]
    _print_items("\n=== input for turn 2 (tail) ===", items2)

    print("\n=== turn 2 ===")
    out2 = Runner.run_sync(agent, items2)
    print("final_output:", out2.final_output)

    items3 = out2.to_input_list()
    _print_items("\n=== to_input_list() after turn 2 (tail) ===", items3)

    return 0


if __name__ == "__main__":
    sys.exit(main())

