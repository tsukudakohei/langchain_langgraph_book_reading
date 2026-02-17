# ch04 docker-check

章4（RAG）向けの「動作確認スクリプト雛形」です。

## 依存関係

まずは ch04/ch05 用の追加依存を入れてください。

```bash
pip install -r requirements.txt
```

## DRY_RUN（APIキー無し）モード

`DRY_RUN=1` を付けると、OpenAIなどの外部APIを呼ばずに動かします。

```bash
DRY_RUN=1 python docker-check/ch04/00_smoke.py
DRY_RUN=1 python docker-check/ch04/01_build_vectorstore.py
DRY_RUN=1 python docker-check/ch04/02_rag_chain_lcel.py --query "このリポジトリの目的は？"
```

## 実API（OpenAI）モード

`.env` に `OPENAI_API_KEY=...` を設定してから実行。

```bash
python docker-check/ch04/01_build_vectorstore.py --source repo
python docker-check/ch04/02_rag_chain_lcel.py --query "このリポジトリは何をするため？"
python docker-check/ch04/03_rag_agent_create_agent.py --query "章4の要点を3つで"
```

## 生成物（ローカル永続）

Chromaの永続DBはデフォルトで `.chroma/ch04/` に作られます。
必要なら `.gitignore` に `.chroma/` を追加してください。
