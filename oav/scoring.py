"""Score a model answer against ground truth per category.

Categories and truth formats (see data/labels.csv):
  dial        truth = number, tolerance column gives +/- allowed
  readout     truth = digit string, compared after stripping non-digits
  date        truth = ISO date, day may be absent (YYYY-MM) ; any format in the answer is accepted
  label_pick  truth = left | right
  medication  truth = number
  button      truth = "row col" words, e.g. "top left", "middle centre"
"""
import re

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
CANT = re.compile(r"(can'?t tell|cannot tell|can not tell|unable to|not visible|not clear|unclear|can'?t see|cannot see|cannot determine|can'?t determine|not possible to)", re.I)
NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


def is_cant_tell(answer: str) -> bool:
    return bool(CANT.search(answer or ""))


def numbers(text: str) -> list[float]:
    return [float(n.replace(",", ".")) for n in NUM.findall(text or "")]


def parse_date(text: str):
    """Return (year, month, day|None) from the first date-looking thing in text, else None."""
    t = (text or "").lower()
    # 2026-03-12 or 2026/03/12
    m = re.search(r"(20\d\d)[-/.](\d{1,2})[-/.](\d{1,2})", t)
    if m:
        return int(m[1]), int(m[2]), int(m[3])
    # 12 mar 2026, 12 march 26, mar 12 2026
    m = re.search(r"(\d{1,2})\s*[-/. ]?\s*([a-z]{3})[a-z]*\.?\s*[-/. ,]?\s*(\d{2,4})", t)
    if m and m[2] in MONTHS:
        return _year(m[3]), MONTHS[m[2]], int(m[1])
    m = re.search(r"([a-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{2,4})", t)
    if m and m[1] in MONTHS:
        return _year(m[3]), MONTHS[m[1]], int(m[2])
    # 12/03/2026 or 12.03.26 (day first, as printed on the labels in this set)
    m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", t)
    if m:
        return _year(m[3]), int(m[2]), int(m[1])
    # mar 2026 / 03/2026 / 03-26
    m = re.search(r"([a-z]{3})[a-z]*\.?\s+(\d{4})", t)
    if m and m[1] in MONTHS:
        return int(m[2]), MONTHS[m[1]], None
    m = re.search(r"(\d{1,2})[./-](\d{2,4})", t)
    if m:
        return _year(m[2]), int(m[1]), None
    return None


def _year(s: str) -> int:
    y = int(s)
    return y + 2000 if y < 100 else y


def _truth_date(truth: str):
    parts = truth.split("-")
    return int(parts[0]), int(parts[1]), (int(parts[2]) if len(parts) > 2 else None)


def match(answer: str, truth: str, category: str, tolerance: float = 0.0) -> bool:
    a = (answer or "").strip()
    if category in ("dial", "medication"):
        nums = numbers(a)
        return bool(nums) and abs(nums[0] - float(truth)) <= tolerance
    if category == "readout":
        digits = re.findall(r"\d[\d:.,]*\d|\d", a)
        want = re.sub(r"\D", "", truth)
        return bool(digits) and re.sub(r"\D", "", digits[0]) == want
    if category == "date":
        got = parse_date(a)
        if not got:
            return False
        ty, tm, td = _truth_date(truth)
        gy, gm, gd = got
        return gy == ty and gm == tm and (td is None or gd == td)
    if category == "label_pick":
        words = re.findall(r"[a-z]+", a.lower())
        first = next((w for w in words if w in ("left", "right")), None)
        return first == truth
    if category == "button":
        al = a.lower()
        row, col = truth.split()
        row_ok = row in al
        col_ok = col in al or (col == "centre" and ("center" in al or "middle" in al))
        return row_ok and col_ok
    raise ValueError(category)


def words_before_answer(answer: str, truth: str, category: str, tolerance: float = 0.0) -> int | None:
    """How many words the user hears before the correct answer appears. None if never.

    Slides a four word window over the answer and returns the first offset at which
    the window alone matches the truth, so a correct value buried in a description is found.
    """
    toks = (answer or "").split()
    for i in range(len(toks)):
        if match(" ".join(toks[i:i + 4]), truth, category, tolerance):
            return i
    return None


def word_count(answer: str) -> int:
    return len((answer or "").split())
