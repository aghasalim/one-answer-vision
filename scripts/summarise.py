"""Aggregate results/raw.csv into results/summary.csv (per regime x category) and results/by_blur.csv."""
import csv
import os
import sys
from collections import defaultdict
from statistics import mean, median

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oav.generate import CATEGORIES  # noqa: E402
from oav.prompts import REGIMES  # noqa: E402


def load(path="results/raw.csv"):
    return list(csv.DictReader(open(path)))


def agg(rows):
    n = len(rows)
    wb = [int(r["words_before"]) for r in rows if r["words_before"] not in ("", "None")]
    return {
        "n": n,
        "accuracy": round(sum(int(r["correct"]) for r in rows) / n, 3) if n else "",
        "cant_tell_rate": round(sum(int(r["cant_tell"]) for r in rows) / n, 3) if n else "",
        "mean_words": round(mean(int(r["words"]) for r in rows), 1) if n else "",
        "median_words_before": median(wb) if wb else "",
        "mean_words_before": round(mean(wb), 1) if wb else "",
        "median_latency_s": round(median(float(r["latency_s"]) for r in rows), 2) if n else "",
        "mean_latency_s": round(mean(float(r["latency_s"]) for r in rows), 2) if n else "",
    }


def main(raw="results/raw.csv"):
    rows = load(raw)
    by = defaultdict(list)
    for r in rows:
        by[(r["regime"], r["category"])].append(r)
        by[(r["regime"], "all")].append(r)
    with open("results/summary.csv", "w", newline="") as f:
        w = None
        for regime in REGIMES:
            for cat in list(CATEGORIES) + ["all"]:
                row = {"regime": regime, "category": cat, **agg(by[(regime, cat)])}
                if w is None:
                    w = csv.DictWriter(f, fieldnames=list(row))
                    w.writeheader()
                w.writerow(row)
    blur = defaultdict(list)
    for r in rows:
        blur[(r["regime"], r["blur"])].append(r)
    with open("results/by_blur.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["regime", "blur", "n", "accuracy"])
        w.writeheader()
        for regime in REGIMES:
            for b in ("0", "1", "2"):
                rs = blur[(regime, b)]
                w.writerow({"regime": regime, "blur": b, "n": len(rs),
                            "accuracy": round(sum(int(r["correct"]) for r in rs) / len(rs), 3) if rs else ""})
    print(open("results/summary.csv").read())


if __name__ == "__main__":
    main(*sys.argv[1:])
