# EPUB版（発行時点）→ 2026年1月時点へのアップデート観点メモ

本書（『LangChainとLangGraphによる RAG・AIエージェント［実践］』）のEPUB版（発行時点）の内容を前提に、**2026年1月時点**の OpenAI / LangChain / LangGraph 周辺の主要な差分と、章ごとの影響箇所を整理したメモ。

## 要点（古く見えやすい主因）

1. OpenAIの推奨が Chat Completions 中心 → **Responses API 中心**に移っている
2. モデル世代が GPT‑4o(2024) → **GPT‑5.x(2025–2026)**中心に移っている
3. LangChain/LangGraphが **v1 系へ**（API整理・エージェントAPI刷新・セキュリティ更新あり） ([OpenAI Platform][1])

---

## 前提（2026年基準の“土台”）

### OpenAI：Responses API + GPT‑5系が基本線

- **Responses API は「新規プロジェクト推奨」**で、Chat Completionsは“サポートは継続”だが主役ではない。 ([OpenAI Platform][1])
- **GPT‑5.2 / GPT‑5 mini / GPT‑5 nano** などの“世代”が中心で、Reasoning（推論）量や出力冗長性（verbosity）を**APIパラメータで制御**する前提。 ([OpenAI Platform][2])
- `chatgpt-4o-latest` のような **ChatGPTスナップショット系は廃止・置換が明確に発生**しうる（例：`chatgpt-4o-latest` スナップショットは 2026-02-17 で削除、置換は `gpt-5.1-chat-latest`）。教材のモデル名が“たまたま動く”状態だと、この手の変更で詰みやすい。 ([OpenAI Platform][3])
- Assistants APIは **Responses APIに統合される流れが確定**しており、移行ガイド/サンセット日程も明示されている（2026-08-26 shut down）。 ([OpenAI Platform][4])

---

## 依存関係の“現代版”テンプレ（pip install 行の置き換え）

EPUB内では `openai==1.40.6`、`langchain-core==0.3.0`、`langgraph==0.2.22`、`langgraph-checkpoint==1.0.11` などが出てくるが、2026年1月時点では **v1 系に揃える**のが安全（API整理と互換性の都合）。 ([PyPI][5])

### requirements.txt（最小構成例）

```txt
# OpenAI
openai

# LangChain / LangGraph (v1系)
langchain==1.2.7
langchain-core==1.2.7
langchain-openai==1.1.7
langgraph==1.0.7
langgraph-prebuilt==1.0.7

# Checkpointing（EPUBに合わせるなら必要）
langgraph-checkpoint==4.0.0
langgraph-checkpoint-sqlite
langgraph-checkpoint-postgres

# RAG周辺（EPUBで使うもの）
langchain-text-splitters==1.0.0
langchain-chroma==1.0.0
langchain-community   # 必要な場合のみ（ツール/リトリーバ等で参照があるなら）
rank-bm25==0.2.2
tavily-python==0.7.11

# 観測・評価（EPUB後半）
langsmith==0.6.1
```

根拠（主要パッケージの現行版）：

- `langchain==1.2.7`（2026-01-23） ([PyPI][5])
- `langchain-core==1.2.7`（2026-01-09） ([PyPI][5])
- `langchain-openai==1.1.7`（2026-01-07） ([PyPI][6])
- `langgraph==1.0.7` / `langgraph-prebuilt==1.0.7`（2026-01-22） ([PyPI][7])
- `langgraph-checkpoint==4.0.0`（2025-11-24） ([PyPI][8])
- `langsmith==0.6.1`（2026-01-06） ([PyPI][9])

---

## 注意：langgraph-checkpoint の旧版はリスク（1.0.11 を置き換える）

EPUBの導線には `langgraph-checkpoint==1.0.11` が登場するが、**langgraph-checkpoint 3.0.0 未満にはRCE（任意コード実行）につながりうる脆弱性**があり、3.0.0以上へのアップグレードが推奨されている。更新するなら 4.x へ寄せるのが無難。 ([GitHub][10])

---

## 第2章（OpenAIのチャットAPI基礎）差分：Chat Completions → Responses API

### 従来例（Chat Completions）

```python
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":"..."}],
)
print(response.choices[0].message.content)
```

### 置き換え案（Responses API：最小）

```python
from openai import OpenAI
client = OpenAI()

resp = client.responses.create(
    model="gpt-5-mini",
    input="...",
)
print(resp.output_text)
```

Responses APIは **文字列inputでもOK**、戻り値は `output_text` ヘルパが使える、など“作り”が異なる。 ([OpenAI Platform][1])

### 置き換え案（GPT‑5.2の推論量/冗長性を制御）

```python
from openai import OpenAI
client = OpenAI()

resp = client.responses.create(
    model="gpt-5.2",
    input="複雑な問い…",
    reasoning={"effort": "medium"},     # none/low/medium/high/xhigh 等
    text={"verbosity": "low"},          # low/medium/high
)
print(resp.output_text)
```

`reasoning.effort` や `text.verbosity` が明示的にドキュメント化されている。 ([OpenAI Platform][2])

### モデル選定メモ（教材内の記述差し替え候補）

- 基本：RAGや通常の業務アプリは `gpt-5-mini` から始める（速度/コスト/性能バランス） ([OpenAI Platform][2])
- 難しい推論・長手順・エージェントタスク：`gpt-5.2`、さらに必要なら `gpt-5.2-pro` ([OpenAI Platform][2])
- ChatGPT追従用途：`gpt-5.2-chat-latest` 等。ただし **スナップショット廃止が起きる**ため本番依存は避ける（注意書きがあると安全）。 ([OpenAI Platform][3])

---

## 第4〜6章（LangChain基礎〜LCEL〜高度なRAG）差分：LangChain v1 前提へ

LangChain v1では **`langchain` 名前空間が整理され**、エージェントの核になるビルディングブロックに寄せられた。古い便利機能（legacy chains / 一部retrievers / hub等）は **`langchain-classic` に移動**という前提。 ([LangChain Docs][11])

### 影響（最小差分）

- `langchain_core` / `langchain_openai` をすでに使っている箇所は、全体を書き換えずに済む可能性が高い
- v1移行で出がちなポイント
  - エージェント生成APIが刷新（後述：create_agent） ([LangChain Docs][11])
  - 返り値の型や“標準コンテンツ（content blocks）”が強化され、メッセージがより構造化される ([LangChain Docs][11])

### ChatOpenAIのモデル名更新（ノートブックを動かしやすくする）

```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

→ まずは以下のように更新：

```python
llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
```

※LangChain側が内部でどのOpenAI APIプリミティブを使うかは統合パッケージの実装に依存するが、教材の主眼（RAG/LCEL/Graph）としてはモデル名更新だけで効果が出やすい。OpenAIとしては新規はResponses推奨。 ([OpenAI Platform][1])

---

## 第9〜11章（LangGraphでエージェント〜チーム〜Agentic RAG）差分：LangGraph v1 + create_agent 移行

### LangGraph v1 の中心概念（Graph API / Streaming / Interrupt）

v1では **ストリーミング**や **human-in-the-loop（interrupt）**がより“定番API”として整理されている。 ([LangChain Docs][12])

### prebuilt の `create_react_agent` は将来性の観点で注意

LangChain v1移行ガイドでは、従来推奨だった `langgraph.prebuilt.create_react_agent` から、**`langchain.agents.create_agent` へ移行**するよう明示されている（import path も含む）。 ([LangChain Docs][11])

旧：

```python
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(model, tools=tools, prompt=...)
```

新（考え方の差分）：

- import が `langchain.agents` へ
- `prompt` が `system_prompt` へ
- 動的プロンプトやフックは middleware で扱う
  …など、APIの設計思想が変わる。 ([LangChain Docs][11])

### チェックポインタは安全な系列へ差し替え必須

保存/永続化（MemorySaver / SqliteSaver / PostgresSaver 等）の説明がある箇所は、**langgraph-checkpoint を新しい系列へ**寄せる必要がある（前述の脆弱性の都合）。 ([GitHub][10])

---

## 第6章・第11章（RAG / Agentic RAG）差分：モデル世代に合わせた微調整

RAG構成（分割→埋め込み→ベクタ検索→コンテキスト注入）は通用する。加えて、GPT‑5世代前提では追記が有用な観点がある。

### 埋め込みモデル：text-embedding-3-(small/large) は現役

`text-embedding-3-small` は現行のモデル一覧にも掲載されており、「古くて使えない」類ではない。 ([OpenAI Platform][13])

### 改善の比重：長コンテキストより “精度設計 + 評価”

推論量も制御できるため、RAGの改善は以下の3点セットで回す方が伸びやすい。

- retrieval精度（chunk設計・検索戦略）
- generation精度（回答フォーマット・根拠提示・引用粒度）
- 評価（回帰テスト）

([OpenAI Platform][2])

---

## 第7〜8章（LangSmith / LLM-as-a-judge評価）差分：トレーシング前提の強化

方針は通用するが、2026年の実務では「最初からトレーシングON」が基本になりがち。

- 例：環境変数で `LANGSMITH_TRACING=true` を設定してトレーシング開始、など。 ([LangChain Docs][14])
- `langsmith` SDK自体も更新されている（0.6.1）。 ([PyPI][9])

---

## 章ごとの差し替えメモ（最短ルートの整理）

**第1章**

- 追記：モデル世代（GPT‑5系）と Responses API が基本線、という現在地。 ([OpenAI Platform][2])

**第2章**

- 置換：Chat Completions API → Responses API（コード差し替え）。 ([OpenAI Platform][1])
- 追記：`reasoning.effort` / `text.verbosity` という“現代のチューニング軸”。 ([OpenAI Platform][2])
- 注意書き：ChatGPTスナップショット系は廃止が起きる。 ([OpenAI Platform][3])

**第3章**

- 追記：構造化出力は Responses 側だとAPI形が変わる（`response_format` → `text.format` 等）。 ([OpenAI Platform][1])

**第4〜6章**

- 置換：依存関係をLangChain v1系へ（requirements更新）。 ([PyPI][5])
- 注意：v1でlegacy機能は `langchain-classic` に移動。 ([LangChain Docs][11])

**第9〜11章**

- 置換：LangGraph v1へ。 ([PyPI][7])
- 置換：`create_react_agent` 前提の説明 → `create_agent`（またはGraph API自作）へ。 ([LangChain Docs][11])
- 必須：`langgraph-checkpoint` を安全な系列へ。 ([GitHub][10])

**第12章**

- “仕様書生成エージェント”はモデル性能向上に合わせて、出力形式の厳格化（構造化）と回帰テスト（LangSmith）を強化すると価値が上がる。 ([OpenAI Platform][1])

---

[1]: https://platform.openai.com/docs/guides/migrate-to-responses "https://platform.openai.com/docs/guides/migrate-to-responses"
[2]: https://platform.openai.com/docs/guides/latest-model "https://platform.openai.com/docs/guides/latest-model"
[3]: https://platform.openai.com/docs/deprecations "https://platform.openai.com/docs/deprecations"
[4]: https://platform.openai.com/docs/assistants/migration "https://platform.openai.com/docs/assistants/migration"
[5]: https://pypi.org/project/langchain/ "https://pypi.org/project/langchain/"
[6]: https://pypi.org/project/langchain-openai/ "https://pypi.org/project/langchain-openai/"
[7]: https://pypi.org/project/langgraph/ "https://pypi.org/project/langgraph/"
[8]: https://pypi.org/project/langgraph-checkpoint/ "https://pypi.org/project/langgraph-checkpoint/"
[9]: https://pypi.org/project/langsmith/ "https://pypi.org/project/langsmith/"
[10]: https://github.com/advisories/GHSA-wwqv-p2pp-99h5 "https://github.com/advisories/GHSA-wwqv-p2pp-99h5"
[11]: https://docs.langchain.com/oss/python/migrate/langchain-v1 "https://docs.langchain.com/oss/python/migrate/langchain-v1"
[12]: https://docs.langchain.com/oss/python/langgraph/graph-api "https://docs.langchain.com/oss/python/langgraph/graph-api"
[13]: https://platform.openai.com/docs/models "https://platform.openai.com/docs/models"
[14]: https://docs.langchain.com/langsmith/env-var "https://docs.langchain.com/langsmith/env-var"

