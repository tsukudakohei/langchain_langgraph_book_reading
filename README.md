# LangChainとLangGraphによる RAG・AIエージェント［実践］ 輪読会

本リポジトリは、書籍『LangChainとLangGraphによる RAG・AIエージェント［実践］』の輪読会用の作業スペースです。

## 重要
- 本のEPUBファイルは、このリポジトリにアップロードしないでください（コミットしないでください）。

## 実行環境（Docker）

第1〜第4章（API基礎 / Chat Completions / Responses / LangChain基礎）向けの学習環境を、Dockerで再現できるようにしています。  
OpenAIは**新規プロジェクトではResponses APIを推奨**しているため、以降の説明はResponses中心です。  
（参考: https://platform.openai.com/docs/guides/responses-vs-chat-completions ）

### 1) APIキーの用意（Gitには入れない）

`.env.example` をコピーして `.env` を作成し、APIキーを入れてください。

```bash
cp .env.example .env
```

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

※ `.env` は `.gitignore` 済みです。

### 2) docker compose でビルド（推奨）

```bash
UID="$(id -u)" GID="$(id -g)" docker compose build
```

OpenAI Python SDKは `openai==2.20.0` に固定しています。  
（参考: https://pypi.org/project/openai/ ）

LangChain / LangGraph も `Dockerfile` でバージョン固定しています（第4章向け）。

### 3) コンテナ起動（シェルに入る）

```bash
UID="$(id -u)" GID="$(id -g)" docker compose run --rm study
```

### 4) APIキーなしでの検証（DRY_RUN）

APIキーがまだ無い場合は `DRY_RUN=1` を付けて動作確認できます。

```bash
DRY_RUN=1 python docker-check/01_responses.py
```

### 5) サンプルスクリプト（第1〜第3章向け）

```bash
python docker-check/01_responses.py
python docker-check/02_chat_completions.py
python docker-check/03_compare.py
```

### 6) Jupyterを使いたい場合（任意）

```bash
UID="$(id -u)" GID="$(id -g)" docker compose up jupyter
```

起動後はブラウザからアクセスします（`http://localhost:8888`）。  
ポートフォワードは `compose.yaml` で `8888:8888` を設定済みです。

## 第4章（LangChain基礎）

勉強会メモ: `docs/ch04.md`

### サンプルスクリプト（第4章向け）

```bash
sh 4-1.sh
sh 4-2.sh
sh 4-3.sh
sh 4-4.sh
sh 4-5.sh
sh 4-6.sh
sh 4-7.sh
```

APIキーなしでの動作確認:

```bash
DRY_RUN=1 sh 4-1.sh
```

Streaming（ブラウザで確認したい場合）:

```bash
SERVE=1 sh 4-6.sh
```

## 追加トピック（OpenAI Agents SDK）

勉強会メモ: `docs/agents_sdk.md`

```bash
sh 4-8.sh
sh 4-9.sh
sh 4-10.sh
sh 4-11.sh
```

APIキーなしでの動作確認:

```bash
DRY_RUN=1 sh 4-8.sh
```

## 参考リンク
- 書籍（Amazon）: https://www.amazon.co.jp/dp/4297145308
- 出版社（技術評論社）: https://gihyo.jp/book/2024/978-4-297-14530-9
- 参考リポジトリ（GitHub）: https://github.com/tsukudakohei/langchain_langgraph_book_reading
- 輪読会メモ（Figma）: https://www.figma.com/board/XPxxrTFpPkUMvgN1nC6hra/%E7%84%A1%E9%A1%8C?node-id=3-10&t=9cq077FBmWQoDZnw-1
