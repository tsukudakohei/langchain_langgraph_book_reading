from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import (  # type: ignore
    default_chroma_dir,
    env_bool,
    load_dotenv_if_present,
    print_section,
    require_env,
    warn,
)
from _fakes import DeterministicFakeEmbeddings, fake_llm_runnable  # type: ignore


def _ensure_vectorstore(persist_dir: Path, collection: str, dry_run: bool):
    """
    persist_dir が空っぽなら samples で簡易DBを作る（雛形として“とりあえず動く”を優先）。
    """
    marker = persist_dir / "chroma.sqlite3"
    if marker.exists():
        return

    # まだDBが無い場合は簡易作成
    print_section(
        "bootstrap",
        f"""
        persist_dir にDBが見つからないため、サンプル文書でベクトルDBを作成します。
        persist_dir: {persist_dir}
        collection: {collection}
        """,
    )
    from langchain_chroma import Chroma  # type: ignore
    from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
    from langchain_core.documents import Document  # type: ignore

    persist_dir.mkdir(parents=True, exist_ok=True)

    docs = [
        Document(page_content="RAGは検索で取り出した文書断片をコンテキストとしてLLMに渡す手法。", metadata={"source": "bootstrap:rag"}),
        Document(page_content="LCELはRunnableをパイプで合成してチェーンを作る記法。", metadata={"source": "bootstrap:lcel"}),
        Document(page_content="Chromaはローカルでも動くベクトルストア。persist_directoryで永続化できる。", metadata={"source": "bootstrap:chroma"}),
    ]
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
    splits = splitter.split_documents(docs)

    if dry_run:
        embeddings = DeterministicFakeEmbeddings()
    else:
        from langchain_openai import OpenAIEmbeddings  # type: ignore
        embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))

    vs = Chroma(
        collection_name=collection,
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
    )
    vs.add_documents(splits)


def main() -> None:
    load_dotenv_if_present()

    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="このリポジトリの目的は？")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--persist-dir", default="")
    ap.add_argument("--collection", default="ch04")
    ap.add_argument("--show-docs", action="store_true")
    args = ap.parse_args()

    persist_dir = Path(args.persist_dir) if args.persist_dir else default_chroma_dir("ch04")

    dry_run = env_bool("DRY_RUN", False)
    if not dry_run and not require_env("OPENAI_API_KEY"):
        warn("OPENAI_API_KEY が無いので DRY_RUN として実行します。")
        dry_run = True

    try:
        from langchain_chroma import Chroma  # type: ignore
        from langchain_core.output_parsers import StrOutputParser  # type: ignore
        from langchain_core.prompts import ChatPromptTemplate  # type: ignore
        from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough  # type: ignore
    except Exception as e:
        print_section(
            "missing deps",
            f"""
            依存が不足しています: {e}
            pip install -r requirements.txt
            """,
        )
        raise SystemExit(2)

    # “とりあえず動く”優先：DBが無ければbootstrapで作る
    _ensure_vectorstore(persist_dir=persist_dir, collection=args.collection, dry_run=dry_run)

    # embeddings は「登録時」と「検索時」で同じ次元・方式である必要があるため、
    # ここでは dry_run と合わせる（運用では embedding方式は固定して管理する）
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
    retriever = vector_store.as_retriever(search_kwargs={"k": args.k})

    def format_docs(docs) -> str:
        chunks = []
        for i, d in enumerate(docs, 1):
            src = d.metadata.get("source", "unknown")
            chunks.append(f"[{i}] source={src}\n{d.page_content}")
        return "\n\n".join(chunks)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "あなたは輪読会のサポーターです。与えられた context の範囲で答えてください。"),
            ("human", "質問: {question}\n\ncontext:\n{context}\n\n回答:"),
        ]
    )

    if dry_run:
        llm = fake_llm_runnable()
    else:
        from langchain_openai import ChatOpenAI  # type: ignore
        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5-mini"), temperature=0)

    # Runnable合成（LCEL）：docs取得と回答生成を並列に扱えるようにする雛形
    chain = (
        RunnableParallel({"docs": retriever, "question": RunnablePassthrough()})
        | RunnablePassthrough.assign(context=RunnableLambda(lambda x: format_docs(x["docs"])))
        | RunnableParallel(
            {
                "answer": (prompt | llm | StrOutputParser()),
                "docs": RunnableLambda(lambda x: x["docs"]),
            }
        )
    )

    out = chain.invoke(args.query)
    print_section("answer", out["answer"])

    if args.show_docs:
        print_section(
            "retrieved docs",
            "\n\n".join(
                f"- source={d.metadata.get('source','?')}  chars={len(d.page_content)}"
                for d in out["docs"]
            ),
        )

    print_section(
        "notes",
        f"""
        persist_dir: {persist_dir}
        collection: {args.collection}
        dry_run: {dry_run}

        - DRY_RUN=1 の場合: LLMは呼ばず prompt preview を出します
        - 実APIの場合: OPENAI_MODEL / OPENAI_EMBEDDING_MODEL を .env で調整できます
        """,
    )


if __name__ == "__main__":
    main()
