"""Exploratory run 2: sends the corpus and one question through chat completions, with neutral sampling.

Usage: VAST_API_KEY=... python3 -I exploratory/ask_chat_2.py CORPUS QUESTION OUT_PREFIX [MAX_TOKENS]

Writes OUT_PREFIX.answer.txt, OUT_PREFIX.reasoning.txt and OUT_PREFIX.meta.json.
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
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 65536
    body = {
        "model": "vast-10m",
        "max_tokens": limit,
        "messages": [{"role": "user", "content": corpus + "\n\n# THE QUESTION\n\n" + question}],
        "stream": True,
        "stream_options": {"include_usage": True},
        "temperature": 1.0,
        "top_p": 1.0,
        "top_k": 0,
        "min_p": 0.0,
        "repetition_penalty": 1.0,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "seed": 7,
    }
    request = urllib.request.Request(
        BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + os.environ["VAST_API_KEY"], "Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    first = None
    text, thought, usage, finish, other = [], [], None, None, set()
    with urllib.request.urlopen(request, timeout=7200) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            event = json.loads(data)
            usage = event.get("usage") or usage
            for choice in event.get("choices", []):
                delta = choice.get("delta") or {}
                finish = choice.get("finish_reason") or finish
                for key, piece in delta.items():
                    if not piece or not isinstance(piece, str) or key == "role":
                        continue
                    if first is None:
                        first = time.time() - start
                    if key == "content":
                        text.append(piece)
                    elif "reason" in key or "think" in key:
                        thought.append(piece)
                    else:
                        other.add(key)
    took = time.time() - start
    pathlib.Path(out + ".answer.txt").write_text("".join(text))
    pathlib.Path(out + ".reasoning.txt").write_text("".join(thought))
    meta = {"seconds": round(took), "first_token_s": round(first or 0), "finish": finish,
            "usage": usage, "answer_chars": len("".join(text)),
            "reasoning_chars": len("".join(thought)), "other_delta_keys": sorted(other),
            "prompt_chars": len(body["messages"][0]["content"])}
    pathlib.Path(out + ".meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta))


main()
