"""Prompt builders for the three regimes compared in the evaluation."""

REGIMES = ("verbose", "terse", "terse_ocr")

VERBOSE = "Describe this image and answer the question: {q}"

TERSE = (
    "You are helping a blind person. Answer the question with the answer only, "
    "at most six words, no description of the scene, no preamble. "
    "If you cannot tell, say exactly: I can't tell.\n"
    "Question: {q}\nAnswer:"
)

TERSE_OCR = (
    "You are helping a blind person. Answer the question with the answer only, "
    "at most six words, no description of the scene, no preamble. "
    "If you cannot tell, say exactly: I can't tell.\n"
    "Text found in the image by OCR (may contain errors): {ocr}\n"
    "Question: {q}\nAnswer:"
)


def build_prompt(question: str, regime: str = "terse", ocr_text: str | None = None) -> str:
    q = question.strip()
    if regime == "verbose":
        return VERBOSE.format(q=q)
    if regime == "terse":
        return TERSE.format(q=q)
    if regime == "terse_ocr":
        return TERSE_OCR.format(q=q, ocr=(ocr_text or "").strip() or "(none)")
    raise ValueError(f"unknown regime {regime!r}, expected one of {REGIMES}")
