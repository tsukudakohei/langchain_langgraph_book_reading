from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import (  # type: ignore
    default_chroma_dir,
    env_bool,
    load_dotenv_if_present,
    print_section,
    require_env,
    warn,
)
from _fakes import DeterministicFakeEmbeddings  # type: ignore


def _extract_tool_result(result: Any) -> tuple[str, list[Any]]:
    if isinstance(result, tuple) and len(result) == 2:
        return str(result[0]), list(result[1]) if isinstance(result[1], list) else []
    if isinstance(result, dict):
        content = result.get("content", "")
        artifact = result.get("artifact", [])
        return str(content), list(artifact) if isinstance(artifact, list) else []
    if hasattr(result, "content") or hasattr(result, "artifact"):
        content = getattr(result, "content", "")
        artifact = getattr(result, "artifact", [])
        return str(content), list(artifact) if isinstance(artifact, list) else []
    return str(result), []


def main() -> None:
    load_dotenv_if_present()

    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="RAGの要点を3つで。")
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--persist-dir", default="")
    ap.add_argument("--collection", default="ch04")
    args = ap.parse_args()

    persist_dir = Path(args.persist_dir) if args.persist_dir else default_chroma_dir("ch04")

    dry_run = env_bool("DRY_RUN", False)
    has_key = bool(require_env("OPENAI_API_KEY"))
    if not dry_run and not has_key:
        warn("OPENAI_API_KEY が無いので、エージェント実行はスキップし、retrieve tool の単体動作だけ確認します。")
        dry_run = True

    try:
        from langchain_chroma import Chroma  # type: ignore
        from langchain.tools import tool  # type: ignore
        from langchain_core.documents import Document  # type: ignore
    except Exception as e:
        print_section(
            "missing deps",
            f"""
            依存が不足しています: {e}
            pip install -r requirements.txt
            """,
        )
        raise SystemExit(2)

    # embeddings は登録時と揃える（雛形なのでDRY_RUN前提ならFake）
    if dry_run:
        embeddings = DeterministicFakeEmbeddings()
    else:
        from langchain_openai import OpenAIEmbeddings  # type: ignore
        embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))

    vector_store = Chroma(
        collection_name=args.collection,
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
    )

    @tool(response_format="content_and_artifact")
    def retrieve_context(query: str):
        """Retrieve information to help answer a query."""
        retrieved_docs = vector_store.similarity_search(query, k=args.k)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}") for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    if dry_run:
        # tool単体の疎通確認
        content, docs = _extract_tool_result(retrieve_context.invoke({"query": args.query}))
        print_section("tool output (content)", content)
        print_section(
            "tool output (artifact docs)",
            "\n".join(f"- {d.metadata.get('source','?')}" for d in docs),
        )
        print_section(
            "how to run agent",
            """
            エージェントまで動かすには OPENAI_API_KEY が必要です:
              python docker-check/ch04/03_rag_agent_create_agent.py --query "章4の要点は？"
            """,
        )
        return

    # 実API: create_agent で“toolを使うRAG”を体験する
    from langchain.agents import create_agent  # type: ignore
    from langchain_openai import ChatOpenAI  # type: ignore

    model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5-mini"), temperature=0)
    tools = [retrieve_context]
    system_prompt = (
        "あなたは輪読会のサポーター。必要に応じて retrieve_context ツールで文脈を取得して回答してください。"
    )

    agent = create_agent(model, tools, system_prompt=system_prompt)

    print_section("agent query", args.query)
    # LangChain v1 の agent は state を stream できる
    for event in agent.stream({"messages": [{"role": "user", "content": args.query}]}, stream_mode="values"):
        event["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()
