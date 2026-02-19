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


def main() -> None:
    load_dotenv_if_present()

    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="Runnableとは何？")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--persist-dir", default="")
    ap.add_argument("--collection", default="ch04")
    args = ap.parse_args()

    dry_run = env_bool("DRY_RUN", False)
    if not dry_run and not require_env("OPENAI_API_KEY"):
        warn("OPENAI_API_KEY が無いので DRY_RUN として実行します。")
        dry_run = True

    persist_dir = Path(args.persist_dir) if args.persist_dir else default_chroma_dir("ch04")

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

    # embeddings を揃える（雛形なのでDRY_RUNに追従）
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
        return "\n\n".join(
            f"- {d.metadata.get('source','?')}\n{d.page_content}"
            for d in docs
        )

    prompt = ChatPromptTemplate.from_template(
        "あなたは技術輪読会のサポーター。\n\n質問: {question}\n\n参考(context):\n{context}\n\n短く要点で答えて。"
    )

    llm = fake_llm_runnable() if dry_run else __real_llm()

    # 章5らしく RunnableParallel / assign を強調した構成
    chain = (
        RunnableParallel({"docs": retriever, "question": RunnablePassthrough()})
        | RunnablePassthrough.assign(context=RunnableLambda(lambda x: format_docs(x["docs"])))
        | (prompt | llm | StrOutputParser())
    )

    ans = chain.invoke(args.query)
    print_section("answer", ans)
    print_section("notes", f"persist_dir={persist_dir}  collection={args.collection}  dry_run={dry_run}")


def __real_llm():
    from langchain_openai import ChatOpenAI  # type: ignore

    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5-mini"), temperature=0)


if __name__ == "__main__":
    main()
