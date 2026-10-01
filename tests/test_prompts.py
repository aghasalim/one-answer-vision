import pytest

from oav.prompts import REGIMES, build_prompt


def test_terse_prompt_contains_question_and_escape_hatch():
    p = build_prompt("what temperature is the oven set to", "terse")
    assert "what temperature is the oven set to" in p
    assert "I can't tell" in p
    assert "six words" in p


def test_verbose_prompt_asks_for_description():
    assert "Describe" in build_prompt("q", "verbose")


def test_ocr_prompt_includes_text():
    assert "BBE 12/2027" in build_prompt("q", "terse_ocr", "BBE 12/2027")
    assert "(none)" in build_prompt("q", "terse_ocr", None)


def test_unknown_regime():
    with pytest.raises(ValueError):
        build_prompt("q", "nope")


def test_regimes():
    assert REGIMES == ("verbose", "terse", "terse_ocr")
