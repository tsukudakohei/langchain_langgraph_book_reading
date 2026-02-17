# ch05 docker-check

章5（Runnable / LCEL）向けの動作確認スクリプト雛形です。

## 依存関係

```bash
pip install -r requirements.txt
```

## Runnableの基礎（APIキー無しでも可）

```bash
python docker-check/ch05/00_runnable_basics.py
```

## RunnableParallel を使った “RAGチェーンの形” を確認（DRY_RUNあり）

```bash
DRY_RUN=1 python docker-check/ch05/01_runnable_parallel_rag.py --query "RAGとは？"
```

## Tavily vs OpenAI web search（任意）

```bash
python docker-check/ch05/02_web_search_compare.py --query "LangChain v1 Runnable とは？"
```
