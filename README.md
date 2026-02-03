# LangChainとLangGraphによる RAG・AIエージェント［実践］ 輪読会

本リポジトリは、書籍『LangChainとLangGraphによる RAG・AIエージェント［実践］』の輪読会用の作業スペースです。

## 重要
- 本のEPUBファイルは、このリポジトリにアップロードしないでください（コミットしないでください）。

## 実行環境（Docker）

第1〜第3章（API基礎 / Chat Completions / Responses）向けの学習環境を、Dockerで再現できるようにしています。  
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

### 2) Dockerイメージをビルド

```bash
docker build \
  --build-arg UID="$(id -u)" \
  --build-arg GID="$(id -g)" \
  -t ai-study:base .
```

OpenAI Python SDKは `openai==2.16.0` に固定しています。  
（参考: https://pypi.org/project/openai/ ）

### 3) コンテナ起動（シェルに入る）

```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)":/workspace \
  -w /workspace \
  ai-study:base
```

### 4) APIキーなしでの検証（DRY_RUN）

APIキーがまだ無い場合は `DRY_RUN=1` を付けて動作確認できます。

```bash
DRY_RUN=1 python scripts/01_responses.py
```

### 5) サンプルスクリプト（第1〜第3章向け）

```bash
python scripts/01_responses.py
python scripts/02_chat_completions.py
python scripts/03_compare.py
```

### 6) Jupyterを使いたい場合（任意）

```bash
docker build \
  --build-arg UID="$(id -u)" \
  --build-arg GID="$(id -g)" \
  --build-arg INSTALL_JUPYTER=1 \
  -t ai-study:base .
```

```bash
docker run --rm -it \
  --env-file .env \
  -p 8888:8888 \
  -v "$(pwd)":/workspace \
  -w /workspace \
  ai-study:base
```

コンテナ内で：

```bash
jupyter lab --ip 0.0.0.0 --no-browser --NotebookApp.token=''
```

## 参考リンク
- 書籍（Amazon）: https://www.amazon.co.jp/dp/4297145308
- 出版社（技術評論社）: https://gihyo.jp/book/2024/978-4-297-14530-9
- 参考リポジトリ（GitHub）: https://github.com/tsukudakohei/langchain_langgraph_book_reading
- 輪読会メモ（Figma）: https://www.figma.com/board/XPxxrTFpPkUMvgN1nC6hra/%E7%84%A1%E9%A1%8C?node-id=3-10&t=9cq077FBmWQoDZnw-1
