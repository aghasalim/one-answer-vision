"""Synthetic test set generator. Deterministic for a given seed.

Six categories, each image has one question and one exact ground truth.
Every image gets a blur level (0, 1, 2), a rotation, an exposure factor and optional clutter,
all drawn from the seeded RNG and written to labels.csv so results can be sliced by them.
"""
import csv
import math
import os
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

FONT_DIR = "/System/Library/Fonts/Supplemental"
FONTS = ["Arial.ttf", "Arial Bold.ttf", "Arial Narrow.ttf", "Courier New.ttf", "Georgia.ttf",
         "Verdana.ttf", "DIN Alternate Bold.ttf", "Tahoma.ttf"]
SIZE = 640
CATEGORIES = ("dial", "readout", "date", "label_pick", "medication", "button")
BLUR_RADIUS = {0: 0.0, 1: 1.6, 2: 3.2}


def font(rng, size, name=None):
    name = name or rng.choice(FONTS)
    path = os.path.join(FONT_DIR, name)
    if not os.path.exists(path):
        return ImageFont.load_default(size)
    return ImageFont.truetype(path, size)


def canvas(rng):
    bg = tuple(rng.randint(170, 240) for _ in range(3))
    img = Image.new("RGB", (SIZE, SIZE), bg)
    return img, ImageDraw.Draw(img)


def clutter(rng, draw):
    for _ in range(rng.randint(2, 6)):
        x, y = rng.randint(0, SIZE), rng.randint(0, SIZE)
        w, h = rng.randint(30, 160), rng.randint(10, 80)
        col = tuple(rng.randint(60, 200) for _ in range(3))
        draw.rectangle([x, y, x + w, y + h], fill=col)
    for _ in range(rng.randint(0, 3)):
        draw.line([rng.randint(0, SIZE), rng.randint(0, SIZE), rng.randint(0, SIZE), rng.randint(0, SIZE)],
                  fill=(rng.randint(0, 120),) * 3, width=rng.randint(2, 6))


def degrade(rng, img, blur, rotation, exposure):
    if rotation:
        img = img.rotate(rotation, resample=Image.BICUBIC, expand=False, fillcolor=(120, 120, 120))
    if exposure != 1.0:
        img = ImageEnhance.Brightness(img).enhance(exposure)
    if BLUR_RADIUS[blur]:
        img = img.filter(ImageFilter.GaussianBlur(BLUR_RADIUS[blur]))
    # mild sensor noise
    px = img.load()
    for _ in range(SIZE * 3):
        x, y = rng.randrange(SIZE), rng.randrange(SIZE)
        r, g, b = px[x, y]
        d = rng.randint(-25, 25)
        px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))
    return img


# ---------------- categories ----------------

DIALS = [
    ("oven", 50, 250, 10, 10, "What temperature is the oven dial set to, in degrees?", "°C"),
    ("thermostat", 10, 30, 1, 1, "What temperature is the thermostat dial set to?", "°C"),
    ("washer", 1, 12, 1, 0, "Which programme number is the washing machine dial pointing at?", ""),
]


def gen_dial(rng, draw):
    kind, lo, hi, step, tol, q, unit = rng.choice(DIALS)
    value = rng.randrange(lo, hi + 1, step)
    cx, cy, r = SIZE // 2, SIZE // 2, 220
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 30, 30) if rng.random() < 0.5 else (235, 235, 235),
                 outline=(0, 0, 0), width=4)
    dark = draw._image.getpixel((cx, cy))[0] < 100
    ink = (240, 240, 240) if dark else (20, 20, 20)
    f = font(rng, 22, "Arial.ttf")
    sweep = 270
    n = (hi - lo) // step
    label_every = max(1, n // 10)
    for i in range(n + 1):
        ang = math.radians(135 + sweep * i / n)
        v = lo + i * step
        major = i % label_every == 0
        x1, y1 = cx + (r - 10) * math.cos(ang), cy + (r - 10) * math.sin(ang)
        x2, y2 = cx + (r - (28 if major else 18)) * math.cos(ang), cy + (r - (28 if major else 18)) * math.sin(ang)
        draw.line([x1, y1, x2, y2], fill=ink, width=3 if major else 1)
        if major:
            tx, ty = cx + (r - 52) * math.cos(ang), cy + (r - 52) * math.sin(ang)
            draw.text((tx, ty), str(v), fill=ink, font=f, anchor="mm")
    ang = math.radians(135 + sweep * (value - lo) / (hi - lo))
    knob = 90
    draw.ellipse([cx - knob, cy - knob, cx + knob, cy + knob], fill=(90, 90, 90) if dark else (200, 200, 200),
                 outline=ink, width=2)
    px, py = cx + (knob - 4) * math.cos(ang), cy + (knob - 4) * math.sin(ang)
    draw.line([cx, cy, px, py], fill=(220, 40, 40), width=8)
    draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(220, 40, 40))
    draw.text((cx, cy + r + 36), f"{kind.upper()} {unit}".strip(), fill=(20, 20, 20), font=f, anchor="mm")
    return q, str(value), tol


READOUTS = [
    ("microwave", lambda rng: f"{rng.randint(0, 19)}:{rng.randint(0, 59):02d}", "What time is left on the microwave timer?"),
    ("scale", lambda rng: f"{rng.randint(40, 120)}.{rng.randint(0, 9)}", "What weight does the scale show?"),
    ("thermostat", lambda rng: f"{rng.randint(15, 29)}.{rng.choice('05')}", "What temperature does the thermostat display show?"),
    ("oven", lambda rng: f"{rng.randrange(100, 260, 5)}", "What temperature does the oven display show?"),
]

SEG = {  # a b c d e f g
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg", "5": "acdfg", "6": "acdefg",
    "7": "abc", "8": "abcdefg", "9": "abcdfg",
}


def seven_seg(draw, x, y, ch, h, on, off):
    w, t = h * 0.55, h * 0.12
    segs = {
        "a": [x + t, y, x + w - t, y + t], "b": [x + w - t, y + t, x + w, y + h / 2 - t / 2],
        "c": [x + w - t, y + h / 2 + t / 2, x + w, y + h - t], "d": [x + t, y + h - t, x + w - t, y + h],
        "e": [x, y + h / 2 + t / 2, x + t, y + h - t], "f": [x, y + t, x + t, y + h / 2 - t / 2],
        "g": [x + t, y + h / 2 - t / 2, x + w - t, y + h / 2 + t / 2],
    }
    lit = SEG.get(ch, "")
    for s, box in segs.items():
        draw.rectangle(box, fill=on if s in lit else off)
    return w


def gen_readout(rng, draw):
    kind, make, q = rng.choice(READOUTS)
    text = make(rng)
    styles = [((60, 255, 90), (20, 40, 20), (10, 15, 10)), ((255, 60, 40), (40, 15, 10), (8, 8, 8)),
              ((25, 25, 25), (170, 180, 160), (150, 160, 140))]
    on, off, panel = rng.choice(styles)
    h = rng.randint(120, 200)
    pw = int(len(text) * h * 0.72 + 60)
    x0, y0 = (SIZE - pw) // 2, (SIZE - h) // 2 - 20
    draw.rectangle([x0 - 30, y0 - 50, x0 + pw + 30, y0 + h + 50], fill=panel, outline=(50, 50, 50), width=6)
    x = x0 + 30
    for ch in text:
        if ch == ":":
            draw.ellipse([x + 8, y0 + h * 0.3, x + 8 + h * 0.1, y0 + h * 0.3 + h * 0.1], fill=on)
            draw.ellipse([x + 8, y0 + h * 0.65, x + 8 + h * 0.1, y0 + h * 0.65 + h * 0.1], fill=on)
            x += h * 0.3
        elif ch == ".":
            draw.ellipse([x + 4, y0 + h - h * 0.12, x + 4 + h * 0.12, y0 + h], fill=on)
            x += h * 0.25
        else:
            x += seven_seg(draw, x, y0, ch, h, on, off) + h * 0.15
    draw.text((SIZE // 2, y0 + h + 90), kind.upper(), fill=(30, 30, 30), font=font(rng, 24, "Arial.ttf"), anchor="mm")
    return q, text, 0


MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def gen_date(rng, draw):
    y, m = rng.randint(2025, 2028), rng.randint(1, 12)
    d = rng.randint(1, 28) if rng.random() < 0.75 else None
    prefix = rng.choice(["BEST BEFORE", "BBE", "EXP", "USE BY", "Best before end", "EXPIRY"])
    if d is None:
        fmt = rng.choice([f"{m:02d}/{y}", f"{MONTH_NAMES[m-1]} {y}", f"{m:02d}-{y % 100:02d}", f"{y}-{m:02d}"])
        truth = f"{y}-{m:02d}"
    else:
        fmt = rng.choice([f"{d:02d}/{m:02d}/{y}", f"{d:02d}.{m:02d}.{y % 100:02d}", f"{d:02d} {MONTH_NAMES[m-1]} {y}",
                          f"{y}-{m:02d}-{d:02d}", f"{d:02d}{MONTH_NAMES[m-1]}{y % 100:02d}"])
        truth = f"{y}-{m:02d}-{d:02d}"
    # a label patch with some other printed lines so the date has to be found
    f_small = font(rng, rng.randint(16, 22))
    f_date = font(rng, rng.randint(30, 48))
    lx, ly = rng.randint(40, 120), rng.randint(60, 200)
    draw.rectangle([lx, ly, lx + 500, ly + 300], fill=(250, 250, 245), outline=(80, 80, 80), width=2)
    product = rng.choice(["Semi skimmed milk 1L", "Greek style yoghurt", "Wholemeal bread", "Orange juice",
                          "Chicken breast fillets", "Cheddar cheese 200g"])
    draw.text((lx + 20, ly + 20), product, fill=(0, 0, 0), font=f_small)
    draw.text((lx + 20, ly + 50), rng.choice(["Keep refrigerated", "Store in a cool dry place", "Once opened use within 3 days"]),
              fill=(0, 0, 0), font=f_small)
    draw.text((lx + 20, ly + 80), f"LOT {rng.randint(1000, 99999)}", fill=(0, 0, 0), font=f_small)
    draw.text((lx + 20, ly + 140), prefix, fill=(0, 0, 0), font=f_small)
    draw.text((lx + 20, ly + 170), fmt, fill=(0, 0, 0), font=f_date)
    draw.text((lx + 20, ly + 250), f"Net weight {rng.choice(['250g', '500g', '1kg', '1L'])}", fill=(0, 0, 0), font=f_small)
    return "What is the best before or expiry date on this label?", truth, 0


PAIRS = [("Oat milk", "Soy milk"), ("Paracetamol", "Ibuprofen"), ("Salt", "Sugar"), ("Chicken stock", "Beef stock"),
         ("Baking powder", "Baking soda"), ("Whole milk", "Skimmed milk"), ("Decaf coffee", "Regular coffee"),
         ("Dishwasher tablets", "Washing tablets")]


def gen_label_pick(rng, draw):
    a, b = rng.choice(PAIRS)
    target = rng.choice([a, b])
    left, right = (a, b) if rng.random() < 0.5 else (b, a)
    f = font(rng, rng.randint(26, 36))
    for i, name in enumerate((left, right)):
        x = 40 + i * 310
        col = tuple(rng.randint(120, 230) for _ in range(3))
        draw.rectangle([x, 120, x + 250, 520], fill=col, outline=(30, 30, 30), width=3)
        draw.rectangle([x + 20, 200, x + 230, 320], fill=(250, 250, 250))
        for j, w in enumerate(name.split()):
            draw.text((x + 125, 230 + j * 44), w, fill=(10, 10, 10), font=f, anchor="mm")
        draw.text((x + 125, 420), rng.choice(["500 ml", "1 L", "200 g", "Family size"]), fill=(20, 20, 20),
                  font=font(rng, 22, "Arial.ttf"), anchor="mm")
    truth = "left" if target == left else "right"
    return f"Which box is the {target.lower()}, the left one or the right one?", truth, 0


MEDS = [("Amoxicillin", "capsules", [250, 500]), ("Paracetamol", "tablets", [500]), ("Ibuprofen", "tablets", [200, 400]),
        ("Metformin", "tablets", [500, 850]), ("Atorvastatin", "tablets", [10, 20, 40]), ("Lisinopril", "tablets", [5, 10, 20])]


def gen_medication(rng, draw):
    name, form, strengths = rng.choice(MEDS)
    mg = rng.choice(strengths)
    per_dose = rng.choice([1, 1, 2])
    times = rng.choice([1, 2, 3, 4])
    lx, ly = rng.randint(30, 90), rng.randint(60, 160)
    draw.rectangle([lx, ly, lx + 540, ly + 340], fill=(255, 255, 250), outline=(60, 60, 60), width=2)
    f_h = font(rng, 30, rng.choice(["Arial Bold.ttf", "Arial.ttf", "Verdana.ttf"]))
    f = font(rng, 24, rng.choice(["Arial.ttf", "Courier New.ttf", "Tahoma.ttf"]))
    draw.text((lx + 20, ly + 20), rng.choice(["Greenway Pharmacy", "Town Centre Pharmacy", "Hillside Chemist"]),
              fill=(0, 0, 0), font=f)
    draw.text((lx + 20, ly + 60), f"{name} {mg} mg {form}", fill=(0, 0, 0), font=f_h)
    draw.text((lx + 20, ly + 120), f"Take {per_dose} {form[:-1] if per_dose == 1 else form} {times} times a day",
              fill=(0, 0, 0), font=f_h)
    draw.text((lx + 20, ly + 170), rng.choice(["with food", "with water", "do not exceed stated dose"]), fill=(0, 0, 0), font=f)
    draw.text((lx + 20, ly + 220), f"Qty {per_dose * times * rng.choice([5, 7, 14])}", fill=(0, 0, 0), font=f)
    draw.text((lx + 20, ly + 260), f"Patient: {rng.choice(['A. Smith', 'J. Brown', 'M. Lee', 'R. Khan'])}", fill=(0, 0, 0), font=f)
    draw.text((lx + 20, ly + 300), f"Dispensed {rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/2026", fill=(0, 0, 0), font=f)
    qs = [(f"How many {form} per dose?", per_dose), ("How many times a day should it be taken?", times),
          (f"What is the strength in mg?", mg)]
    q, truth = rng.choice(qs)
    return q, str(truth), 0


BUTTONS = ["START", "STOP", "+30 SEC", "DEFROST", "CLOCK", "POWER", "TIMER", "MENU", "CANCEL", "KIDS LOCK", "AUTO", "GRILL"]
ROWS, COLS = ["top", "middle", "bottom"], ["left", "centre", "right"]


def gen_button(rng, draw):
    names = rng.sample(BUTTONS, 9)
    target = rng.choice(names)
    px, py = rng.randint(60, 140), rng.randint(60, 140)
    draw.rectangle([px - 30, py - 30, px + 450, py + 450], fill=(70, 70, 75), outline=(30, 30, 30), width=5)
    f = font(rng, rng.randint(16, 20), rng.choice(["Arial.ttf", "Arial Bold.ttf", "DIN Alternate Bold.ttf"]))
    for i, name in enumerate(names):
        r, c = divmod(i, 3)
        x, y = px + c * 145, py + r * 145
        draw.rounded_rectangle([x, y, x + 130, y + 130], radius=14, fill=(200, 200, 205), outline=(20, 20, 20), width=2)
        draw.text((x + 65, y + 65), name, fill=(10, 10, 10), font=f, anchor="mm")
    r, c = divmod(names.index(target), 3)
    q = f"Where is the {target.title()} button? Answer with row and column, for example top left or middle centre."
    return q, f"{ROWS[r]} {COLS[c]}", 0


GENERATORS = {"dial": gen_dial, "readout": gen_readout, "date": gen_date, "label_pick": gen_label_pick,
              "medication": gen_medication, "button": gen_button}


def generate(out_dir: str, seed: int = 20260101, per_category: int = 26) -> list[dict]:
    rng = random.Random(seed)
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    rows = []
    for cat in CATEGORIES:
        for i in range(per_category):
            img, draw = canvas(rng)
            use_clutter = rng.random() < 0.4
            if use_clutter:
                clutter(rng, draw)
            q, truth, tol = GENERATORS[cat](rng, draw)
            blur = i % 3
            rotation = rng.choice([0, 0, rng.uniform(-15, 15)])
            exposure = rng.choice([1.0, 1.0, rng.uniform(0.35, 0.7), rng.uniform(1.2, 1.5)])
            img = degrade(rng, img, blur, rotation, exposure)
            name = f"{cat}_{i:03d}.png"
            img.save(os.path.join(img_dir, name), optimize=True)
            rows.append({"image": name, "category": cat, "question": q, "truth": truth, "tolerance": tol,
                         "blur": blur, "rotation": round(rotation, 1), "exposure": round(exposure, 2),
                         "clutter": int(use_clutter)})
    with open(os.path.join(out_dir, "labels.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "data"
    rows = generate(out)
    print(f"wrote {len(rows)} images to {out}/images and {out}/labels.csv")
