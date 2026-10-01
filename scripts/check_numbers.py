"""Re-derive every number quoted in README.md from results/summary.csv and results/by_blur.csv.

The README embeds numbers as <!-- num:KEY -->value<!-- /num -->. This script recomputes KEY and
fails if the value in the README does not match. Run from the repo root.
"""
import csv
import re
import sys


def load():
    summ = {(r["regime"], r["category"]): r for r in csv.DictReader(open("results/summary.csv"))}
    blur = {(r["regime"], r["blur"]): r for r in csv.DictReader(open("results/by_blur.csv"))}
    return summ, blur


def derive(summ, blur):
    out = {}
    for (reg, cat), r in summ.items():
        out[f"acc_{reg}_{cat}"] = f"{float(r['accuracy']) * 100:.0f}"
        out[f"cant_{reg}_{cat}"] = f"{float(r['cant_tell_rate']) * 100:.0f}"
        out[f"words_{reg}_{cat}"] = r["mean_words"]
        out[f"wb_median_{reg}_{cat}"] = r["median_words_before"]
        out[f"lat_median_{reg}_{cat}"] = f"{float(r['median_latency_s']):.1f}"
        out[f"n_{reg}_{cat}"] = r["n"]
    for (reg, b), r in blur.items():
        out[f"blur{b}_{reg}"] = f"{float(r['accuracy']) * 100:.0f}"
    return out


def main():
    summ, blur = load()
    want = derive(summ, blur)
    readme = open("README.md").read()
    found = re.findall(r"<!-- num:([\w]+) -->([^<]*)<!-- /num -->", readme)
    if not found:
        sys.exit("no tagged numbers found in README.md")
    bad = 0
    for key, val in found:
        if key not in want:
            print(f"UNKNOWN {key}")
            bad += 1
        elif str(want[key]) != val.strip():
            print(f"MISMATCH {key}: README says {val.strip()!r}, data says {want[key]!r}")
            bad += 1
    print(f"checked {len(found)} numbers, {bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
