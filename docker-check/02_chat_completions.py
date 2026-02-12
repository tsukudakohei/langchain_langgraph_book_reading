from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def check_api_key() -> bool:
    """APIキーのチェック。問題があればFalseを返す。"""
    if os.getenv("DRY_RUN") == "1":
        print("DRY_RUN=1 のため API 呼び出しをスキップしました。")
        return False

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "OPENAI_API_KEY が未設定です。.env を作成して設定してください。\n"
            "例: cp .env.example .env"
        )
        return False

    return True


def chat_completion() -> None:
    """通常のChat Completions API呼び出し"""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "こんにちは！私はジョンと言います！"},
        ],
    )
    print(response.to_json(indent=2))


def chat_completion_stream() -> None:
    """ストリーミングでChat Completions API呼び出し"""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "こんにちは！私はジョンと言います！"},
        ],
        stream=True,
    )
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content is not None:
            print(content, end="", flush=True)
    print()


def chat_completion_json_mode() -> None:
    """JSONモードでChat Completions API呼び出し"""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": '人物一覧を次の JSON 形式で出力してください。\n{"people": ["aaa", "bbb"]}',
            },
            {
                "role": "user",
                "content": "桃太郎に出てくる人物を教えてください。",
            },
        ],
        response_format={"type": "json_object"},
    )
    print(response.choices[0].message.content)


def chat_completion_vision() -> None:
    """Vision（画像入力）でChat Completions API呼び出し"""
    from openai import OpenAI

    client = OpenAI()
    image_url = "https://raw.githubusercontent.com/yoshidashingo/langchain-book/main/assets/cover.jpg"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "画像を説明してください。"},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    )
    print(response.choices[0].message.content)


def get_current_weather(location: str, unit: str = "fahrenheit") -> str:
    """地域を指定して天気を得られる関数（ダミー実装）"""
    import json

    if "tokyo" in location.lower() or "東京" in location:
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "san francisco" in location.lower():
        return json.dumps(
            {"location": "San Francisco", "temperature": "72", "unit": unit}
        )
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})


def chat_completion_function_calling() -> None:
    """Function calling（関数呼び出し）のデモ"""
    import json

    from openai import OpenAI

    client = OpenAI()

    # LLMが使用できる関数の一覧を定義
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    messages = [{"role": "user", "content": "東京の天気はどうですか？"}]

    # 1回目: LLMに関数を使うか判断させる
    print("=== 1回目: tools + messages を送信 ===")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
    )
    print(response.to_json(indent=2))

    assistant_message = response.choices[0].message

    # LLMが関数を呼び出したいと判断した場合
    if assistant_message.tool_calls:
        tool_call = assistant_message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        # 実際の関数を実行
        print(f"\n=== プログラム側で関数を実行 ===")
        print(f"関数名: {function_name}")
        print(f"引数: {function_args}")
        function_result = get_current_weather(**function_args)
        print(f"実行結果: {function_result}")

        # 2回目: 関数の結果をLLMに渡して最終応答を得る
        messages.append(assistant_message)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_result,
            }
        )

        print("\n=== 2回目: 関数の実行結果を含めて再度API呼び出し ===")
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
        )
        print(final_response.to_json(indent=2))


if __name__ == "__main__":
    if not check_api_key():
        sys.exit(0)

    # chat_completion()
    # # ストリーミングでの応答を試す
    # chat_completion_stream()
    # # # JSONモードでの応答を試す
    # chat_completion_json_mode()
    # # # Vision（画像入力）での応答を試す
    # chat_completion_vision()
    # # Function calling（関数呼び出し）を試す
    chat_completion_function_calling()
