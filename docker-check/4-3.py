from __future__ import annotations

import sys

from _common import ensure_openai_api_key, get_openai_model, is_dry_run


def main() -> int:
    if is_dry_run():
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        print("このスクリプトは LangChain Messages の最小例です。")
        return 0

    if not ensure_openai_api_key():
        return 0

    from langchain.chat_models import init_chat_model
    from langchain.messages import HumanMessage, SystemMessage

    llm = init_chat_model(
        get_openai_model(),
        model_provider="openai",
        temperature=0,
    )

    messages = [
        SystemMessage(content="あなたは日本語で、短く丁寧に答えるアシスタントです。"),
        HumanMessage(content="LangChainのMessagesとは何？ 1文で説明して。"),
    ]
    resp = llm.invoke(messages)
    print(resp.content)
    return 0


if __name__ == "__main__":
    sys.exit(main())

