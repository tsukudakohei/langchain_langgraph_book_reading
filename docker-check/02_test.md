docker compose run --rm study python docker-check/02_chat_completions.py

実行結果

```
{
  "id": "chatcmpl-D5paojoKuHlW1otYVOiepTyLGUQLi",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "logprobs": null,
      "message": {
        "content": "こんにちは、ジョンさん！お話しできてうれしいです。今日はどんなことをお話ししましょうか？",
        "refusal": null,
        "role": "assistant",
        "annotations": []
      }
    }
  ],
  "created": 1770282334,
  "model": "gpt-4o-mini-2024-07-18",
  "object": "chat.completion",
  "service_tier": "default",
  "system_fingerprint": "fp_f4ae844694",
  "usage": {
    "completion_tokens": 28,
    "prompt_tokens": 25,
    "total_tokens": 53,
    "completion_tokens_details": {
      "accepted_prediction_tokens": 0,
      "audio_tokens": 0,
      "reasoning_tokens": 0,
      "rejected_prediction_tokens": 0
    },
    "prompt_tokens_details": {
      "audio_tokens": 0,
      "cached_tokens": 0
    }
  }
}
```

## レスポンスの解説

| フィールド                   | 説明                                   |
| ---------------------------- | -------------------------------------- |
| `id`                         | リクエストの一意識別子                 |
| `choices`                    | モデルの応答（複数返せるが通常1つ）    |
| `choices[0].message.content` | **実際の応答テキスト**（これがメイン） |
| `choices[0].finish_reason`   | 終了理由（`stop`=正常終了）            |
| `model`                      | 使用されたモデル名                     |
| `usage`                      | トークン使用量                         |

**usage（課金に関係）**:

- `prompt_tokens`: 入力に使ったトークン数（25）
- `completion_tokens`: 応答に使ったトークン数（28）
- `total_tokens`: 合計（53）

実際のアプリでは `response.choices[0].message.content` で応答テキストだけを取り出すことが多い。

[~/workspace/langchain_langgraph_book_reading] <kohei.tsukuda@bizlink.io>
=> % docker compose run --rm study python docker-check/02_chat_completions.py 18:13:17
{
"id": "chatcmpl-D5piOrsNE4ELMwIMcr0ZPAYRGvbx1",
"choices": [
{
"finish_reason": "stop",
"index": 0,
"logprobs": null,
"message": {
"content": "こんにちは、ジョンさん！お話しできて嬉しいです。今日はどんなことをお話ししましょうか？",
"refusal": null,
"role": "assistant",
"annotations": []
}
}
],
"created": 1770282804,
"model": "gpt-4o-mini-2024-07-18",
"object": "chat.completion",
"service_tier": "default",
"system_fingerprint": "fp_f4ae844694",
"usage": {
"completion_tokens": 27,
"prompt_tokens": 25,
"total_tokens": 52,
"completion_tokens_details": {
"accepted_prediction_tokens": 0,
"audio_tokens": 0,
"reasoning_tokens": 0,
"rejected_prediction_tokens": 0
},
"prompt_tokens_details": {
"audio_tokens": 0,
"cached_tokens": 0
}
}
}
こんにちは、ジョンさん！お会いできて嬉しいです。今日はどんなことをお話ししましょうか？

## Function calling（関数呼び出し）

LLMに「使える関数の一覧」を伝えておき、LLMに「関数を使いたい」という判断をさせる機能。
**LLMが関数を実行するわけではない**（判断を返すだけ）。

### 処理の流れ

```
┌─────────────────┐                    ┌─────────────────────┐
│  Pythonなどの    │                    │  Chat Completions   │
│  プログラム       │                    │       API           │
└────────┬────────┘                    └──────────┬──────────┘
         │                                        │
         │  1. tools + messages を送信             │
         │  ─────────────────────────────────────>│
         │                                        │
         │  2. 「get_current_weather を使いたい    │
         │      引数は {"location": "東京"}」      │
         │  <─────────────────────────────────────│
         │                                        │
         │  3. プログラムが関数を実行              │
         │     get_current_weather("東京")        │
         │                                        │
         │  4. 関数の実行結果を含めて再度API呼び出し │
         │  ─────────────────────────────────────>│
         │                                        │
         │  5. 関数の実行結果を踏まえて最終応答     │
         │  <─────────────────────────────────────│
```

### 別名

| フレームワーク/API | 呼び方           |
| ------------------ | ---------------- |
| OpenAI             | Function calling |
| LangChain          | Tool calling     |
| Anthropic          | Tool use         |

### 1回目のAPIレスポンス（関数を使いたいという判断）

```json
{
  "choices": [
    {
      "finish_reason": "tool_calls",
      "message": {
        "content": null,
        "tool_calls": [
          {
            "id": "call_xxx",
            "function": {
              "arguments": "{\"location\":\"東京\"}",
              "name": "get_current_weather"
            },
            "type": "function"
          }
        ]
      }
    }
  ]
}
```

**ポイント**:

| フィールド                        | 値             | 説明                             |
| --------------------------------- | -------------- | -------------------------------- |
| `finish_reason`                   | `"tool_calls"` | 関数を呼びたいと判断した         |
| `message.content`                 | `null`         | テキスト応答なし（関数呼び出し） |
| `tool_calls[0].function.name`     | 関数名         | 呼び出したい関数                 |
| `tool_calls[0].function.arguments`| JSON文字列     | 関数の引数                       |
| `tool_calls[0].id`                | 一意のID       | 2回目の呼び出しで使用            |

### 2回目のAPIレスポンス（最終応答）

関数の実行結果を含めて再度APIを呼び出すと、最終応答が返ってくる。

```json
{
  "choices": [
    {
      "finish_reason": "stop",
      "message": {
        "content": "東京の現在の天気は摂氏約 -12 度です。",
        "role": "assistant"
      }
    }
  ]
}
```

**ポイント**:

| フィールド        | 値         | 説明                           |
| ----------------- | ---------- | ------------------------------ |
| `finish_reason`   | `"stop"`   | 通常の応答完了                 |
| `message.content` | テキスト   | 関数結果を踏まえた最終応答     |

関数の戻り値 `{"temperature": "10", "unit": "fahrenheit"}` をもとに、LLMが自然言語で回答を生成（10°F → -12°C に変換）。
