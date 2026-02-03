from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    if os.getenv("DRY_RUN") == "1":
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        return 0

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(
            "OPENAI_API_KEY が未設定です。.env を作成して設定してください。\n"
            "例: cp .env.example .env"
        )
        return 0

    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": "ping"}],
    )
    print(response.choices[0].message.content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
