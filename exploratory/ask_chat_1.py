"""Exploratory run 1: sends one prompt file through chat completions and streams the answer to a file.

Usage: VAST_API_KEY=... python3 -I exploratory/ask_chat_1.py PROMPT_FILE ANSWER_FILE [MAX_TOKENS]
"""
import json
import os
import pathlib
import sys
import time
import urllib.request

BASE = os.environ.get("VAST_BASE_URL", "https://demo.voltropy.com/v1")


def main():
    prompt = pathlib.Path(sys.argv[1]).read_text()
    answer = pathlib.Path(sys.argv[2])
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 32768
    body = {
        "model": "vast-10m",
        "max_tokens": limit,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "temperature": 0.2,
        "top_p": 1.0,
    }
    request = urllib.request.Request(
        BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + os.environ["VAST_API_KEY"], "Content-Type": "application/json"},
        method="POST",
    )
    start = time.time()
    parts = []
    usage = None
    with urllib.request.urlopen(request, timeout=3600) as response:
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
                piece = (choice.get("delta") or {}).get("content")
                if piece:
                    parts.append(piece)
    answer.write_text("".join(parts))
    print(f"chars {len(''.join(parts))} in {time.time() - start:.0f} s; usage {usage}")


main()
