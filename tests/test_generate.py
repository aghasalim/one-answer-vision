import csv
import hashlib
import os

from oav.generate import generate


def _digest(d):
    h = hashlib.sha256()
    for n in sorted(os.listdir(os.path.join(d, "images"))):
        h.update(open(os.path.join(d, "images", n), "rb").read())
    h.update(open(os.path.join(d, "labels.csv"), "rb").read())
    return h.hexdigest()


def test_generator_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    ra = generate(str(a), seed=7, per_category=2)
    rb = generate(str(b), seed=7, per_category=2)
    assert ra == rb
    assert _digest(str(a)) == _digest(str(b))
    assert len(ra) == 12
    rows = list(csv.DictReader(open(a / "labels.csv")))
    assert {r["category"] for r in rows} == {"dial", "readout", "date", "label_pick", "medication", "button"}
    assert all(r["truth"] for r in rows)


def test_different_seed_differs(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    generate(str(a), seed=1, per_category=1)
    generate(str(b), seed=2, per_category=1)
    assert _digest(str(a)) != _digest(str(b))
