from __future__ import annotations

import hashlib
from typing import Iterable


def _bytes_to_floats(b: bytes) -> list[float]:
    # Map each byte to [-1, 1) roughly.
    return [((x - 128) / 128.0) for x in b]


class DeterministicFakeEmbeddings:
    """
    APIキー無しで「ベクトル化っぽい」挙動を再現するための簡易Embeddings。
    LangChainのEmbeddingsプロトコル互換（embed_documents / embed_query）。
    """

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _embed(self, text: str) -> list[float]:
        # blake2b の digest_size は 64 までなので、ブロック連結で任意次元を作る。
        seed = text.encode("utf-8", errors="ignore")
        out = bytearray()
        counter = 0
        while len(out) < self.dim:
            block = hashlib.blake2b(seed + counter.to_bytes(4, "little"), digest_size=64).digest()
            out.extend(block)
            counter += 1
        return _bytes_to_floats(bytes(out[: self.dim]))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def fake_llm_runnable():
    """
    DRY_RUN時の「LLMの代用品」。
    prompt(=ChatPromptValue等)を受け取り、文字列を返す RunnableLambda を返す。
    """
    from langchain_core.runnables import RunnableLambda  # type: ignore

    def _respond(prompt_value) -> str:
        # ChatPromptValue なら to_string() がある
        if hasattr(prompt_value, "to_string"):
            prompt_text = prompt_value.to_string()
        else:
            prompt_text = str(prompt_value)
        preview = prompt_text[:800].replace("\n\n\n", "\n\n")
        return (
            "[DRY_RUN] LLM呼び出しはスキップしました（APIキー無し想定）。\n"
            "---- prompt preview (first 800 chars) ----\n"
            f"{preview}\n"
            "---- end ----\n"
            "※ retrieval の結果や prompt の組み立てができているかを確認してください。"
        )

    return RunnableLambda(_respond)
