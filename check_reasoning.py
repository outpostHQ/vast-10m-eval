"""Sends three tiny requests to see which API makes vast-10m reason. Prints usage and output parts.

Usage: VAST_API_KEY=... python3 -I check_reasoning.py
Our output is in results/reasoning-check.txt.
"""
import json
import os
import urllib.error
import urllib.request

BASE = os.environ.get("VAST_BASE_URL", "https://demo.voltropy.com/v1")
QUESTION = "A train leaves at 9:40 and the trip takes 2 h 35 min. When does it arrive? Answer briefly."
TRIES = [
    ("chat, reasoning_effort high", "/chat/completions",
     {"messages": [{"role": "user", "content": QUESTION}], "max_tokens": 4096, "reasoning_effort": "high"}),
    ("responses, plain", "/responses", {"input": QUESTION, "max_output_tokens": 4096}),
    ("responses, reasoning high", "/responses",
     {"input": QUESTION, "max_output_tokens": 4096, "reasoning": {"effort": "high"}}),
]
for label, path, extra in TRIES:
    body = {"model": "vast-10m", "temperature": 1.0, "top_p": 1.0, **extra}
    request = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": "Bearer " + os.environ["VAST_API_KEY"],
                                              "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            reply = json.load(response)
    except urllib.error.HTTPError as err:
        print(label, "HTTP", err.code, err.read()[:300])
        continue
    usage = reply.get("usage")
    kinds = [item.get("type") for item in reply.get("output", [])] if "output" in reply else None
    text = ""
    if "choices" in reply:
        message = reply["choices"][0]["message"]
        text = message.get("content") or ""
        kinds = sorted(k for k, v in message.items() if v)
    else:
        for item in reply.get("output", []):
            for part in item.get("content", []) or []:
                text += part.get("text", "")
    print(label, "| usage", json.dumps(usage)[:300], "| parts", kinds, "| text", text[:80].replace("\n", " "))
