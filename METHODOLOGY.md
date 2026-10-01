# Methodology

## Question

Does prompting a small local vision language model for a terse, answer-first reply give
blind users a shorter and at least as accurate answer than the default "describe the image"
style, on the kinds of question people on r/Blind say they actually ask (dials, readouts,
dates, picking one of two boxes, medication lines, where a button is)? And does an OCR
pre-pass on the phone's own text recogniser help?

## Test set

`data/` holds 156 synthetic images, 26 per category, made by `oav/generate.py` from a fixed
seed (20260101). Every image has one question and one exact ground truth in
`data/labels.csv`. The six categories:

| category | what is drawn | truth | match rule |
|---|---|---|---|
| dial | oven (50 to 250, step 10), thermostat (10 to 30) or washing machine (1 to 12) dial, red pointer at a known angle | number | first number in the answer within tolerance (10 for oven, 1 for thermostat, 0 for washer) |
| readout | 7-segment panel: microwave timer, scale, thermostat, oven | digit string | first digit group in the answer, non-digits stripped, exact |
| date | label with product lines, a lot number and a best-before line in one of 9 print formats | ISO date, day optional | first date-like string parsed, year and month must match, day too if the truth has one |
| label_pick | two boxes side by side with similar product names | left or right | first of "left"/"right" in the answer |
| medication | pharmacy label with strength and dosing line | number | first number in the answer, exact |
| button | 3x3 panel of labelled buttons | "row column" | row word and column word both present |

Each image also gets, from the same RNG: blur level 0, 1 or 2 (Gaussian radius 0, 1.6, 3.2,
cycling by index so each level has the same count per category), a rotation (two thirds
none, else up to 15 degrees), an exposure factor (half untouched, else dark 0.35 to 0.7 or
bright 1.2 to 1.5), clutter rectangles with probability 0.4, and light pixel noise. All of
these are columns in `labels.csv`.

The set is synthetic. The dials, displays and labels are drawn with PIL, not photographed.
That makes the truth exact and the generator reproducible but it also means the images are
cleaner than any phone photo a blind user would take (no hands, no glare, no perspective,
no partial framing). Numbers here are an upper bound on real performance. Real photos from
blind users are the next step and are not in this repo.

I looked for a free real dataset of 7-segment or dial photos with clear labels and licence
to add as a real subset and did not find one I could use within the session, so there is
no real subset.

## Model

One model: the smallest Qwen3-VL that Ollama serves (`qwen3-vl:4b`), run through the
Ollama HTTP API on an Apple M4 with 24 GB, no CUDA. Temperature 0, seed 0, thinking off.
Max new tokens: 300 for the verbose regime, 40 for the terse ones. Nothing is fine tuned.

## Regimes

* `verbose`: "Describe this image and answer the question: Q". This stands in for how
  general assistants behave by default.
* `terse`: a system style instruction asking for the answer only, at most six words,
  no description, and "I can't tell" as the allowed escape.
* `terse_ocr`: same as terse, plus the text that Apple Vision (`VNRecognizeTextRequest`,
  through pyobjc) found in the image, pasted into the prompt as "may contain errors".

Exact prompts are in `oav/prompts.py`.

## Metrics

* accuracy: match rule above, per category and overall.
* I can't tell rate: answer contains one of the refusal phrases in `oav/scoring.py`.
* words: whitespace tokens in the answer.
* words before answer: a four word window slides over the answer; the first offset at
  which the window alone matches the truth. This is what a screen reader user has to sit
  through before hearing the value. Only defined for answers that contain the right value.
* latency: wall clock around the HTTP call, model already loaded (one warm-up call first).
  Another process on the same machine was using Ollama with a different 8B model during the
  run, so latencies are noisier than they would be on an idle machine.

## Threats to validity

* Synthetic images, one model, one machine, one run per image at temperature 0.
* The match rules take the first number or first left/right. A verbose answer that mentions
  a wrong number before the right one is scored wrong. That is deliberate (it is what the
  user hears first) but it does penalise the verbose regime on top of its length.
* Date parsing in the scorer assumes day before month for slash dates, which matches how
  the labels in this set are printed.
* No blind user has used this. The Reddit quotes in the README are the only user input.
