"""Figures from results/summary.csv, results/by_blur.csv and results/raw.csv."""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oav.generate import CATEGORIES  # noqa: E402
from oav.prompts import REGIMES  # noqa: E402

LABEL = {"verbose": "describe (verbose)", "terse": "terse", "terse_ocr": "terse + OCR"}
COL = {"verbose": "#9aa0a6", "terse": "#1f77b4", "terse_ocr": "#2ca02c"}


def main():
    summ = list(csv.DictReader(open("results/summary.csv")))
    blur = list(csv.DictReader(open("results/by_blur.csv")))
    raw = list(csv.DictReader(open("results/raw.csv")))

    # 1 accuracy per category per regime
    fig, ax = plt.subplots(figsize=(9, 4.2))
    cats = list(CATEGORIES) + ["all"]
    wdt = 0.26
    for k, reg in enumerate(REGIMES):
        ys = [float(next(r["accuracy"] for r in summ if r["regime"] == reg and r["category"] == c) or 0) for c in cats]
        ax.bar([i + (k - 1) * wdt for i in range(len(cats))], ys, wdt, label=LABEL[reg], color=COL[reg])
    ax.set_xticks(range(len(cats)), cats)
    ax.set_ylim(0, 1)
    ax.set_ylabel("accuracy (tolerance match)")
    ax.set_title("Accuracy per category and prompt regime")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("results/accuracy_per_category.png", dpi=150)

    # 2 words before answer (verbose vs terse), only answers that were eventually correct
    fig, ax = plt.subplots(figsize=(7, 4))
    data, labels = [], []
    for reg in REGIMES:
        wb = [int(r["words_before"]) for r in raw if r["regime"] == reg and r["words_before"] not in ("", "None")]
        if wb:
            data.append(wb)
            labels.append(f"{LABEL[reg]}\n(n={len(wb)})")
    ax.boxplot(data, tick_labels=labels, showfliers=True)
    ax.set_ylabel("words spoken before the correct value")
    ax.set_title("How much the user has to listen to before the answer")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("results/words_before_answer.png", dpi=150)

    # 3 latency
    fig, ax = plt.subplots(figsize=(7, 4))
    data = [[float(r["latency_s"]) for r in raw if r["regime"] == reg] for reg in REGIMES]
    ax.boxplot(data, tick_labels=[LABEL[r] for r in REGIMES])
    ax.set_ylabel("seconds per question (M4, Ollama)")
    ax.set_title("Latency per question")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("results/latency.png", dpi=150)

    # 4 accuracy vs blur
    fig, ax = plt.subplots(figsize=(6, 4))
    for reg in REGIMES:
        ys = [float(r["accuracy"] or 0) for r in blur if r["regime"] == reg]
        ax.plot([0, 1, 2], ys, marker="o", label=LABEL[reg], color=COL[reg])
    ax.set_xticks([0, 1, 2], ["none", "radius 1.6", "radius 3.2"])
    ax.set_xlabel("gaussian blur")
    ax.set_ylabel("accuracy")
    ax.set_ylim(0, 1)
    ax.set_title("Accuracy vs blur level")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig("results/accuracy_vs_blur.png", dpi=150)
    print("wrote 4 figures to results/")


if __name__ == "__main__":
    main()
