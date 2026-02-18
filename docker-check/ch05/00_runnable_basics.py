from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import load_dotenv_if_present, print_section  # type: ignore


def main() -> None:
    load_dotenv_if_present()

    try:
        from langchain_core.runnables import RunnableGenerator, RunnableLambda, RunnableParallel, RunnablePassthrough  # type: ignore
    except Exception as e:
        print_section(
            "missing deps",
            f"""
            依存が不足しています: {e}
            pip install -r requirements.txt
            """,
        )
        raise SystemExit(2)

    # 1) invoke / batch（関数をRunnable化）
    add_one = RunnableLambda(lambda x: x + 1)
    print_section("invoke", f"add_one.invoke(1) = {add_one.invoke(1)}")
    print_section("batch", f"add_one.batch([1,2,3]) = {add_one.batch([1,2,3])}")

    # 2) パイプ（RunnableSequence相当）：`|` で直列合成
    chain = RunnableLambda(lambda x: x * 2) | RunnableLambda(lambda x: f"result={x}")
    print_section("pipe", f"chain.invoke(21) = {chain.invoke(21)}")

    # 3) dict入力の加工（Passthroughでキーを追加する雛形）
    enrich = RunnablePassthrough.assign(length=lambda x: len(x["text"]))
    out = enrich.invoke({"text": "hello runnable"})
    print_section("passthrough.assign", f"{out}")

    # 4) 並列合成（RunnableParallel）：同じ入力を複数Runnableに流してdictで受け取る
    parallel = RunnableParallel(
        upper=RunnableLambda(lambda x: x["text"].upper()),
        length=RunnableLambda(lambda x: len(x["text"])),
    )
    out2 = parallel.invoke({"text": "parallel"})
    print_section("parallel", f"{out2}")

    # 5) stream（RunnableGeneratorの最小例）
    def gen(_input_iter):
        for token in ["Have", " a", " nice", " day"]:
            yield token

    streamer = RunnableGenerator(gen)
    streamed = list(streamer.stream(None))
    print_section("stream (RunnableGenerator)", f"{streamed}  -> joined: {''.join(streamed)}")

    # 6) 応用例（簡易記法）:
    # dict と lambda は LCEL 内で自動的に Runnable として扱われる。
    triage_chain = (
        {
            "text": lambda x: x["text"].strip(),
            "channel": lambda x: x.get("channel", "chat"),
        }
        | RunnablePassthrough.assign(
            lowered=lambda x: x["text"].lower(),
            length=lambda x: len(x["text"]),
            severity=lambda x: (
                "high"
                if any(k in x["text"].lower() for k in ["error", "fail", "timeout", "障害"])
                else "normal"
            ),
        )
        | RunnablePassthrough().pick(["text", "channel", "length", "severity"])
        | {
            "ticket_title": lambda x: f"[{x['severity'].upper()}] {x['text'][:40]}",
            "route": lambda x: "oncall" if x["severity"] == "high" else "support",
            "summary": lambda x: (
                f"channel={x['channel']} len={x['length']} severity={x['severity']} "
                f"text='{x['text'][:60]}'"
            ),
        }
    )

    triage_in = {
        "text": "API timeout が断続的に発生。15分で3回failしています。",
        "channel": "slack",
    }
    triage_out = triage_chain.invoke(triage_in)
    print_section("practical mini-flow (no API, shorthand LCEL)", f"input={triage_in}\noutput={triage_out}")


if __name__ == "__main__":
    main()
