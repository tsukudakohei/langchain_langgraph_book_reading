# 追加トピック: OpenAI Agents SDK（LangChainとの違い / ハーネス）

この資料は、勉強会で「LangChain（+LangGraph）で同じことをやるとどうなるか？」と比較しながら、OpenAI Agents SDKの設計（特に**ハーネス**）を議論するためのメモです。

## 前提

- APIキーは `.env` に `OPENAI_API_KEY` として保存します（Gitにはコミットしません）
- 任意: `OPENAI_MODEL` を設定すると使用モデルを切り替えできます（未設定なら `gpt-5-mini`）
- APIキーが無い場合でも `DRY_RUN=1` を付けると、API呼び出しなしで雰囲気だけ確認できます

Dockerでビルド:

```bash
UID="$(id -u)" GID="$(id -g)" docker compose build
```

ワンショット実行（推奨）:

```bash
sh 4-8.sh
sh 4-9.sh
sh 4-10.sh
sh 4-11.sh
```

DRY_RUN:

```bash
DRY_RUN=1 sh 4-8.sh
DRY_RUN=1 sh 4-9.sh
DRY_RUN=1 sh 4-10.sh
DRY_RUN=1 sh 4-11.sh
```

## この資料で言う「ハーネス」とは

ここでは「エージェントを“動かすための実行基盤一式”」をハーネスと呼びます。

- `Runner` が回す agent loop（tool callの実行、結果の取り込み、再実行…）
- streaming（トークンのデルタだけでなく、**意味のあるイベント**として観測できる）
- `final_output`（最終出力を、一定の形で取り出せる）
- input items（Responses APIの入力items列）と `to_input_list()`（入力の成長を扱える）
- Sessions（会話履歴の永続化/自動再投入）
- Tracing（観測性。必要なら無効化も可能）

LangChain側でも同様の構成要素は作れますが、Agents SDKはこれらが「Runner中心に最初から一体化」している、という整理で議論します。

## LangChain と Agents SDK の比較（議論の観点）

| 観点 | LangChain（+LangGraph） | Agents SDK |
|---|---|---|
| ループ（tool→結果→再実行） | 部品を組んで作る（Agent/Graph/State/Checkpointerなど） | `Runner` が標準で回す |
| 入力表現 | 多くは messages（System/Human/AI） | 文字列 or input items（Responsesのitems列） |
| メモリ（履歴） | `checkpointer + thread_id`（例: `InMemorySaver`） | `Session` を渡すとRunnerが自動で履歴を扱う |
| ストリーミング | `model.stream(...)` のchunk | `raw_response_event`（デルタ） + `run_item_stream_event`（意味イベント） |
| 観測性 | 実装次第（ログ/トレースを組む） | tracingが標準（無効化も可能） |

## 4.8 Agents SDK: 最小エージェント（LangChain 4.1 と対比）

LangChain側の最小例: `docker-check/4-1.py`  
Agents SDK側の最小例: `docker-check/4-8.py`

### 目的

- `Agent` に instructions（system prompt相当）と tools を渡す
- `Runner.run_sync(...)` で実行する
- 最終出力は `result.final_output` で取る

### 最小概念（用語）

- `Agent`: instructions（方針）+ tools（関数）+ model（LLM）を束ねた「実行単位」
- `function_tool`: Python関数の型/Docstringから、ツールschemaを自動生成するデコレータ
- `Runner`: agent loop（tool call実行→結果取り込み→再実行…）を回す“実行ハーネス”
- `RunResult`: 実行結果（`final_output` / `new_items` / `to_input_list()` などを持つ）
- `final_output`: 「最終的にユーザーへ返す値」を1か所で取り出すためのフィールド

### LangChainだったら / Agents SDKだったら

LangChain（`docker-check/4-1.py`）は `create_agent(...)` を作って `agent.invoke(...)` します（戻りは state 辞書）。

```python
# LangChain (概念)
agent = create_agent(model=..., tools=[...])
out = agent.invoke({"messages": [("user", "...")]})
```

Agents SDK（`docker-check/4-8.py`）は `Agent(...)` と `Runner.run_sync(...)` が基本線です（戻りは `RunResult`）。

```python
# Agents SDK (概念)
agent = Agent(name="demo", instructions="...", tools=[...], model="...")
result = Runner.run_sync(agent, "...")
print(result.final_output)
```

### サンプル実行

```bash
sh 4-8.sh
```

DRY_RUN:

```bash
DRY_RUN=1 sh 4-8.sh
```

## 4.9 input items と `to_input_list()`（入力の成長）

Agents SDKは内部的にResponses API（input items）に寄せた入力表現で動きます。

重要ポイント:

- `Runner.run_sync(agent, "文字列")` は、内部で `{"role": "user", "content": "..."}` のような input item に正規化されます
- 1回の実行で生成された「新しい items（メッセージ/ツール呼び出し/ツール出力など）」は、次のターンの入力に取り込めます
- そのための最小APIが `result.to_input_list()` です

この資料では「input items が伸びる」ことが、ハーネスの重要な側面だと捉えます。

### 最小概念（用語）

- input items: Responses APIの入力表現（dictの配列）。最小形は `{"role": "user", "content": "..."}`。
- `to_input_list()`: 「元の入力 + 実行中に増えた items」を**次のターン入力として**再構築するためのAPI。

### サンプル実行

```bash
sh 4-9.sh
```

DRY_RUN:

```bash
DRY_RUN=1 sh 4-9.sh
```

### 見どころ（ログ）

- `to_input_list() after turn 1` の末尾に、モデル出力が input items として追加されている
- `input for turn 2` は、それに user item を足したもの
- `to_input_list() after turn 2` でさらに items が増える

LangChainでも「messages配列を継ぎ足す」ことで似たことはできますが、Agents SDKは **“Responsesのitems列”に揃った中間表現**として扱える点が議論ポイントです。

## 4.10 Sessions（Runnerに履歴管理を委譲）

LangChain側の短期メモリ例: `docker-check/4-5.py`  
Agents SDK側のSessions例: `docker-check/4-10.py`

### 目的

- `SQLiteSession(session_id, db_path)` を作り、`Runner.run_sync(..., session=...)` を渡す
- 2ターン目で「名前を覚えている」ことを確認
- session_id を変えると「別スレッド」になることを確認

### 最小概念（用語）

- `Session`: 会話履歴（input items）を保存/取得するストレージ抽象（Runnerが利用）
- `SQLiteSession`: SessionのSQLite実装（ファイルに永続化できる）

### サンプル実行

```bash
sh 4-10.sh
```

DRY_RUN:

```bash
DRY_RUN=1 sh 4-10.sh
```

### 注意

- `docker-check/agents_sdk_conversations.db` を作成します（Git管理外）
- サンプルは再実行で結果がブレないよう、起動時にセッションをクリアしています

## 4.11 Streaming events（最終出力 + input items の流れまで）

LangChain側のStreaming最小例: `docker-check/4-6.py`  
Agents SDK側のStreaming events例: `docker-check/4-11.py`

### 目的

ストリーミングを2レイヤーで観測し、最後に「最終出力」と「input items の成長」をセットで確認します。

1) raw delta（LLMが出すトークン断片）

- `raw_response_event` の `data.type == "response.output_text.delta"` を拾って逐次表示

2) 意味イベント（ハーネスが生成するイベント）

- `run_item_stream_event` をログ化
  - `tool_called` / `tool_output`
  - `message_output_created`
  - など

最後に:

- `final_output`
- `to_input_list()`（末尾items）

を表示して「途中の出来事」と「入力の成長」と「最終出力」が繋がっていることを確認します。

### 最小概念（用語）

- `raw_response_event`: モデルが返す“生の”ストリームイベント（例: `response.output_text.delta`）
- `run_item_stream_event`: ハーネスが生成する“意味イベント”（tool呼び出し/出力/メッセージ生成など）
- `RunResultStreaming`: streaming実行の結果。`stream_events()`（async generator）でイベント購読できる

### サンプル実行

```bash
sh 4-11.sh
```

DRY_RUN:

```bash
DRY_RUN=1 sh 4-11.sh
```

### つまずきポイント

- 出力が長い: 末尾だけ表示する（このリポジトリのサンプルもtail表示）
- tracingが気になる/ログが増える:
  - `OPENAI_AGENTS_DISABLE_TRACING=1` で無効化できます（環境変数）
  - Docker経由で確実に渡すなら `.env` に追記（例: `OPENAI_AGENTS_DISABLE_TRACING=1`）

## ディスカッション用の問い（勉強会向け）

- LangChainでは「自分たちが書く glue code」はどこに出る？ Agents SDKではそれがどこに吸収される？
- `to_input_list()` のような “items列” は、messagesより理解しやすい？ それとも抽象度が高すぎる？
- 「状態（state）」は誰が持つべき？（LangGraphのstate/schema vs Agents SDKのsession/items）
- ストリーミングUIを作るとき、`raw_response_event` と `run_item_stream_event` のどちらを主に使うべき？
- tracingがデフォルトONであることは、開発体験とプライバシーの観点でどう評価する？

## 公式リンク

- リポジトリ: https://github.com/openai/openai-agents-python
- Docs（トップ）: https://openai.github.io/openai-agents-python/
- Running agents: https://openai.github.io/openai-agents-python/running_agents/
- Streaming: https://openai.github.io/openai-agents-python/streaming/
- Sessions: https://openai.github.io/openai-agents-python/sessions/
- Tracing: https://openai.github.io/openai-agents-python/tracing/
