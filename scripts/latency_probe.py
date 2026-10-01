"""Latency of the terse regime on 12 images, with Ollama's own timing fields, to separate
model work from contention with other Ollama jobs on the machine. Writes results/latency_probe.csv."""
import base64
import csv
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oav.prompts import build_prompt  # noqa: E402
from oav.vlm import DEFAULT_MODEL  # noqa: E402

rows = [r for r in csv.DictReader(open("data/labels.csv")) if int(r["image"].split("_")[-1][:3]) < 2]
out = []
for r in rows:
    img = base64.b64encode(open(f"data/images/{r['image']}", "rb").read()).decode()
    body = {"model": DEFAULT_MODEL, "prompt": build_prompt(r["question"], "terse"), "images": [img], "stream": False,
            "options": {"temperature": 0, "num_predict": 40, "seed": 0}}
    t = time.perf_counter()
    d = requests.post("http://localhost:11434/api/generate", json=body, timeout=600).json()
    row = {"image": r["image"], "wall_s": round(time.perf_counter() - t, 2),
           "load_s": round(d.get("load_duration", 0) / 1e9, 2), "prompt_eval_s": round(d.get("prompt_eval_duration", 0) / 1e9, 2),
           "eval_s": round(d.get("eval_duration", 0) / 1e9, 2), "total_s": round(d.get("total_duration", 0) / 1e9, 2),
           "answer": d.get("response", "").strip().replace("\n", " ")}
    out.append(row)
    print(row, flush=True)
with open("results/latency_probe.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
