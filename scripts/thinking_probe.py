"""Negative result: qwen3-vl:4b (thinking variant) ignores think=false in Ollama 0.35.
Run the terse prompt on the first 2 images per category with a large token budget and record
how long it takes and how many tokens it spends before answering. Writes results/thinking_probe.csv."""
import base64
import csv
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oav.prompts import build_prompt  # noqa: E402
from oav.scoring import match  # noqa: E402

rows = list(csv.DictReader(open("data/labels.csv")))
pick = [r for r in rows if int(r["image"].split("_")[-1][:3]) < 2]
out = []
for r in pick:
    img = base64.b64encode(open(f"data/images/{r['image']}", "rb").read()).decode()
    body = {"model": "qwen3-vl:4b", "prompt": build_prompt(r["question"], "terse"), "images": [img], "stream": False,
            "think": False, "options": {"temperature": 0, "num_predict": 2000, "seed": 0}}
    t = time.perf_counter()
    d = requests.post("http://localhost:11434/api/generate", json=body, timeout=900).json()
    dt = time.perf_counter() - t
    ans = d.get("response", "").strip()
    row = {"image": r["image"], "category": r["category"], "truth": r["truth"], "answer": ans.replace("\n", " "),
           "correct": int(match(ans, r["truth"], r["category"], float(r["tolerance"]))),
           "eval_count": d.get("eval_count"), "thinking_words": len(d.get("thinking", "").split()),
           "latency_s": round(dt, 2), "done_reason": d.get("done_reason")}
    out.append(row)
    print(row, flush=True)
with open("results/thinking_probe.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
