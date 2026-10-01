import pytest

from oav.scoring import is_cant_tell, match, parse_date, words_before_answer


@pytest.mark.parametrize("ans,truth,tol,ok", [
    ("180", "180", 10, True), ("about 185 degrees", "180", 10, True), ("200", "180", 10, False),
    ("The oven is set to 170.", "180", 10, True), ("I can't tell", "180", 10, False), ("", "180", 10, False),
])
def test_dial_tolerance(ans, truth, tol, ok):
    assert match(ans, truth, "dial", tol) is ok


@pytest.mark.parametrize("ans,truth,ok", [
    ("12:30", "12:30", True), ("12.30", "12:30", True), ("1230", "12:30", True), ("12:35", "12:30", False),
    ("72.4 kg", "72.4", True), ("72 kg", "72.4", False), ("The display shows 72.4", "72.4", True),
])
def test_readout(ans, truth, ok):
    assert match(ans, truth, "readout") is ok


@pytest.mark.parametrize("ans,truth,ok", [
    ("12 MAR 2026", "2026-03-12", True), ("12/03/2026", "2026-03-12", True), ("2026-03-12", "2026-03-12", True),
    ("March 12, 2026", "2026-03-12", True), ("12.03.26", "2026-03-12", True), ("13 MAR 2026", "2026-03-12", False),
    ("MAR 2026", "2026-03", True), ("03/2026", "2026-03", True), ("03-26", "2026-03", True), ("04/2026", "2026-03", False),
    ("Best before 12 March 2026.", "2026-03-12", True), ("I can't tell", "2026-03-12", False),
])
def test_date(ans, truth, ok):
    assert match(ans, truth, "date") is ok


def test_parse_date_none():
    assert parse_date("no date here") is None


@pytest.mark.parametrize("ans,truth,ok", [
    ("left", "left", True), ("The left one.", "left", True), ("right", "left", False),
    ("The oat milk is on the right, the soy milk on the left.", "right", True),
])
def test_label_pick(ans, truth, ok):
    assert match(ans, truth, "label_pick") is ok


@pytest.mark.parametrize("ans,truth,ok", [
    ("top left", "top left", True), ("Top row, left column", "top left", True), ("middle centre", "middle centre", True),
    ("middle center", "middle centre", True), ("in the middle", "middle centre", True), ("top right", "top left", False),
])
def test_button(ans, truth, ok):
    assert match(ans, truth, "button") is ok


def test_medication_first_number():
    assert match("2 tablets", "2", "medication") is True
    assert match("500 mg, 2 tablets", "2", "medication") is False


def test_cant_tell():
    assert is_cant_tell("I can't tell")
    assert is_cant_tell("The display is unclear.")
    assert not is_cant_tell("180")


def test_words_before_answer():
    assert words_before_answer("180", "180", "dial", 10) == 0
    long = "The image shows a black oven dial with white markings and a red pointer. It is set to 180 degrees."
    assert words_before_answer(long, "180", "dial", 10) in (14, 15, 16, 17)
    assert words_before_answer("I can't tell", "180", "dial", 10) is None
