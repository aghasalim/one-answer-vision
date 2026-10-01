"""Call a local Ollama vision model and time it."""
import base64
import time

import requests

from .ocr import read_text
from .prompts import build_prompt

OLLAMA = "http://localhost:11434"
DEFAULT_MODEL = "qwen3-vl:4b"


def ask(image_path: str, question: str, regime: str = "terse", model: str = DEFAULT_MODEL,
        num_predict: int | None = None, host: str = OLLAMA) -> dict:
    ocr_text = read_text(image_path) if regime == "terse_ocr" else None
    prompt = build_prompt(question, regime, ocr_text)
    with open(image_path, "rb") as f:
        img = base64.b64encode(f.read()).decode()
    if num_predict is None:
        num_predict = 300 if regime == "verbose" else 40
    body = {
        "model": model,
        "prompt": prompt,
        "images": [img],
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_predict": num_predict, "seed": 0},
    }
    t0 = time.perf_counter()
    r = requests.post(f"{host}/api/generate", json=body, timeout=600)
    r.raise_for_status()
    dt = time.perf_counter() - t0
    data = r.json()
    answer = data.get("response", "").strip()
    return {
        "answer": answer,
        "latency_s": round(dt, 3),
        "eval_count": data.get("eval_count"),
        "ocr_text": ocr_text,
        "regime": regime,
        "model": model,
    }
