from __future__ import annotations

import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlparse

from _common import ensure_openai_api_key, get_openai_model, is_dry_run


def _stream_tokens(prompt: str) -> Iterable[str]:
    if is_dry_run():
        demo = (
            "[DRY_RUN] This is a simulated streaming response.\n"
            "Set OPENAI_API_KEY in .env to stream real tokens.\n"
        )
        for ch in demo:
            time.sleep(0.01)
            yield ch
        return

    if not ensure_openai_api_key():
        return

    from langchain.chat_models import init_chat_model

    llm = init_chat_model(
        get_openai_model(),
        model_provider="openai",
        temperature=0,
    )
    for chunk in llm.stream(prompt):
        # AIMessageChunk.content is usually a growing string fragment.
        text = getattr(chunk, "content", "")
        if not text:
            continue
        yield text


def _run_cli(prompt: str) -> int:
    for token in _stream_tokens(prompt):
        print(token, end="", flush=True)
    print()
    return 0


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_index()
            return
        if parsed.path == "/events":
            qs = parse_qs(parsed.query)
            prompt = (qs.get("prompt") or [""])[0].strip() or "日本語で短いジョークを1つ。"
            self._serve_sse(prompt)
            return

        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"not found")

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Keep console output clean for a study repo.
        return

    def _serve_index(self) -> None:
        path = Path(__file__).parent / "streaming_frontend" / "index.html"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _serve_sse(self, prompt: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        def send(payload: dict) -> None:
            msg = f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()

        try:
            for token in _stream_tokens(prompt):
                send({"type": "token", "text": token})
            send({"type": "end"})
        except BrokenPipeError:
            return
        except Exception as e:  # pragma: no cover
            try:
                send({"type": "error", "message": str(e)})
            except Exception:
                return


def _run_server(host: str, port: int) -> int:
    httpd = ThreadingHTTPServer((host, port), _Handler)
    print(f"Serving on http://{host}:{port}/")
    print("Open in your browser to see streaming updates.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="LangChain streaming demo (CLI + SSE).")
    parser.add_argument("--serve", action="store_true", help="Start a small SSE server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--prompt", default="日本語で短い昔話を1つ作ってください。")
    args = parser.parse_args()

    if args.serve:
        return _run_server(args.host, args.port)
    return _run_cli(args.prompt)


if __name__ == "__main__":
    sys.exit(main())

