from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import (  # type: ignore
    default_chroma_dir,
    env_bool,
    info,
    load_dotenv_if_present,
    print_section,
    require_env,
    warn,
)
from _fakes import DeterministicFakeEmbeddings  # type: ignore


def load_sample_docs():
    from langchain_core.documents import Document  # type: ignore

    return [
        Document(
            page_content="LangChainはLLMアプリを構築するためのフレームワーク。RAGは検索（retrieval）と生成（generation）を組み合わせる。",
            metadata={"source": "sample:rag"},
        ),
        Document(
            page_content="RunnableはLangChainの標準実行インターフェース。invoke/batch/streamで一貫して呼び出せる。",
            metadata={"source": "sample:runnable"},
        ),
        Document(
            page_content="ベクトルDB（例: Chroma）は、文書チャンクの埋め込みベクトルを保存し、類似検索で関連チャンクを返す。",
            metadata={"source": "sample:vectorstore"},
        ),
    ]


def load_repo_docs(repo_root: Path, max_files: int):
    from langchain_core.documents import Document  # type: ignore

    candidates: list[Path] = []
    # なるべく小さく、輪読会に関係しそうなものだけ
    for pat in ["README.md", "epub-diff-*.md", "docker-check/*.py"]:
        candidates.extend(sorted(repo_root.glob(pat)))

    docs = []
    for p in candidates[:max_files]:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        docs.append(
            Document(
                page_content=text,
                metadata={"source": str(p.relative_to(repo_root))},
            )
        )
    return docs


def get_embeddings(dry_run: bool):
    if dry_run:
        return DeterministicFakeEmbeddings(dim=256)

    # 実API: OpenAI embeddings
    from langchain_openai import OpenAIEmbeddings  # type: ignore

    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=model)


def main() -> None:
    load_dotenv_if_present()

    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["samples", "repo"], default="samples")
    ap.add_argument("--persist-dir", default="")
    ap.add_argument("--collection", default="ch04")
    ap.add_argument("--max-files", type=int, default=25)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    persist_dir = Path(args.persist_dir) if args.persist_dir else default_chroma_dir("ch04")
    persist_dir.mkdir(parents=True, exist_ok=True)

    # DRY_RUN=1 ならAPI不要。DRY_RUN=0でもAPIキーが無ければ自動でDRY_RUN扱いにする。
    dry_run = env_bool("DRY_RUN", False)
    if not dry_run and not require_env("OPENAI_API_KEY"):
        warn("OPENAI_API_KEY が無いので DRY_RUN として実行します。必要なら .env を設定してください。")
        dry_run = True

    try:
        from langchain_chroma import Chroma  # type: ignore
        from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
    except Exception as e:
        print_section(
            "missing deps",
            f"""
            依存が不足しています: {e}
            以下を実行してください:
              pip install -r requirements.txt
            """,
        )
        raise SystemExit(2)

    if args.source == "samples":
        docs = load_sample_docs()
    else:
        docs = load_repo_docs(repo_root=repo_root, max_files=args.max_files)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    splits = splitter.split_documents(docs)

    embeddings = get_embeddings(dry_run=dry_run)
    vector_store = Chroma(
        collection_name=args.collection,
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
    )

    vector_store.add_documents(splits)

    # count表示（内部APIは将来変わり得るので try で）
    count = None
    try:
        count = vector_store._collection.count()  # type: ignore[attr-defined]
    except Exception:
        pass

    info(f"persist_dir: {persist_dir}")
    info(f"collection: {args.collection}")
    info(f"dry_run: {dry_run}")
    info(f"docs: {len(docs)}  splits: {len(splits)}  stored_count: {count}")

    print_section(
        "next",
        """
        次はRAGの問い合わせ:
          python docker-check/ch04/02_rag_chain_lcel.py --query "このリポジトリの目的は？"

        APIキー無しで:
          DRY_RUN=1 python docker-check/ch04/02_rag_chain_lcel.py --query "RAGとは？"
        """,
    )


if __name__ == "__main__":
    main()
