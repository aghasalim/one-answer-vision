"""Run the local VLM over data/labels.csv in all three regimes. Appends to results/raw.csv so it can resume."""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oav.prompts import REGIMES  # noqa: E402
from oav.scoring import is_cant_tell, match, word_count, words_before_answer  # noqa: E402
from oav.vlm import DEFAULT_MODEL, ask  # noqa: E402

FIELDS = ["image", "category", "regime", "model", "truth", "tolerance", "blur", "rotation", "exposure", "clutter",
          "answer", "correct", "words", "words_before", "cant_tell", "latency_s", "eval_count", "ocr_text"]


def main(model=DEFAULT_MODEL, out="results/raw.csv", data="data"):
    done = set()
    if os.path.exists(out):
        with open(out) as f:
            done = {(r["image"], r["regime"]) for r in csv.DictReader(f)}
    rows = list(csv.DictReader(open(os.path.join(data, "labels.csv"))))
    new = not os.path.exists(out)
    f = open(out, "a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new:
        w.writeheader()
    # warm the model once so the first measured latency is not a model load
    ask(os.path.join(data, "images", rows[0]["image"]), "what is this", "terse", model, num_predict=5)
    t_start = time.time()
    n = 0
    for regime in REGIMES:
        for r in rows:
            if (r["image"], regime) in done:
                continue
            res = ask(os.path.join(data, "images", r["image"]), r["question"], regime, model)
            tol = float(r["tolerance"])
            ans = res["answer"]
            ok = match(ans, r["truth"], r["category"], tol)
            w.writerow({**{k: r[k] for k in ("image", "category", "truth", "tolerance", "blur", "rotation", "exposure", "clutter")},
                        "regime": regime, "model": model, "answer": ans.replace("\n", " "), "correct": int(ok),
                        "words": word_count(ans), "words_before": words_before_answer(ans, r["truth"], r["category"], tol),
                        "cant_tell": int(is_cant_tell(ans)), "latency_s": res["latency_s"], "eval_count": res["eval_count"],
                        "ocr_text": (res["ocr_text"] or "").replace("\n", " | ")})
            f.flush()
            n += 1
            print(f"{regime:10s} {r['image']:22s} {int(ok)} {res['latency_s']:5.1f}s  {ans[:60]!r}", flush=True)
    print(f"{n} calls in {time.time() - t_start:.0f}s")


if __name__ == "__main__":
    main(*sys.argv[1:])
