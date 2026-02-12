from __future__ import annotations

import sys

from _common import ensure_openai_api_key, get_openai_model, is_dry_run


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは LangChain Models（init_chat_model）の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from langchain.chat_models import init_chat_model

    llm = init_chat_model(
        get_openai_model(),
        model_provider="openai",
        temperature=0,
    )

    one = llm.invoke("1文で自己紹介して。")
    print("=== invoke ===")
    print(one.content)

    batch = llm.batch(
        [
            "猫の豆知識を1つ。",
            "犬の豆知識を1つ。",
        ]
    )
    print("\n=== batch ===")
    for i, msg in enumerate(batch, start=1):
        print(f"[{i}] {msg.content}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

