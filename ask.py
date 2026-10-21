"""Sends the corpus and one question to vast-10m through the Responses API, and records the stream.

Usage: VAST_API_KEY=... python3 -I ask.py CORPUS QUESTION OUT_PREFIX [MAX_OUTPUT_TOKENS]

Writes OUT_PREFIX.answer.txt, OUT_PREFIX.reasoning.txt and OUT_PREFIX.meta.json.
VAST_BASE_URL changes the endpoint; the default is the demo endpoint that we tested.
"""
import json
import os
import pathlib
import sys
import time
import urllib.request

BASE = os.environ.get("VAST_BASE_URL", "https://demo.voltropy.com/v1")


def main():
    corpus = pathlib.Path(sys.argv[1]).read_text()
    question = pathlib.Path(sys.argv[2]).read_text()
    out = sys.argv[3]
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 131072
    body = {
        "model": "vast-10m",
        "input": corpus + "\n\n# THE QUESTION\n\n" + question,
        "max_output_tokens": limit,
        "stream": True,
        "temperature": 1.0,
        "top_p": 1.0,
    }
    request = urllib.request.Request(
        BASE + "/responses",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + os.environ["VAST_API_KEY"], "Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    first = None
    text, thought, kinds, final = [], [], {}, {}
    with urllib.request.urlopen(request, timeout=10800) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            event = json.loads(data)
            kind = event.get("type", "")
            kinds[kind] = kinds.get(kind, 0) + 1
            if kind.endswith(".delta") and isinstance(event.get("delta"), str):
                if first is None:
                    first = time.time() - start
                (thought if "reasoning" in kind else text).append(event["delta"])
            if kind in ("response.completed", "response.incomplete", "response.failed"):
                final = event.get("response", {})
    took = time.time() - start
    pathlib.Path(out + ".answer.txt").write_text("".join(text))
    pathlib.Path(out + ".reasoning.txt").write_text("".join(thought))
    meta = {"seconds": round(took), "first_token_s": round(first or 0), "status": final.get("status"),
            "incomplete": final.get("incomplete_details"), "error": final.get("error"),
            "usage": final.get("usage"), "answer_chars": len("".join(text)),
            "reasoning_chars": len("".join(thought)), "events": kinds, "prompt_chars": len(body["input"])}
    pathlib.Path(out + ".meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: meta[k] for k in ("seconds", "first_token_s", "status", "usage", "answer_chars",
                                           "reasoning_chars")}))


main()
