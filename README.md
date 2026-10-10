# one-answer-vision

You point the camera, ask a question, and get a short answer back, all offline.

I run a small vision language model locally through Ollama and prompt it to answer a blind
user's question with just the value. Then I check whether that short answer is actually
right. The questions are the kind people on r/Blind say they really ask, like reading a dial
or a digital display, finding a best-before date, picking one of two boxes, reading the
dosing line on medication, or finding where a button is.

[![ci](https://github.com/aghasalim/one-answer-vision/actions/workflows/ci.yml/badge.svg)](https://github.com/aghasalim/one-answer-vision/actions/workflows/ci.yml)

## Abstract

The usual assistants describe the whole scene before they get to the number. They also
need internet and run on someone else's server. So I built a tool that sends one image and
one question to `qwen3-vl:4b` on an Apple M4 through Ollama. The prompt asks for only the
answer, in six words or fewer, and the model is allowed to say "I can't tell". I tried three
prompt styles on a synthetic set of 156 labelled images in six categories. The first is the
usual "describe and answer" style. The second is a terse prompt that puts the answer first,
and the third is the terse prompt plus an OCR pass with the Mac's built-in text recogniser.
The results are below. Keep in mind I drew the test images with PIL and didn't photograph
them, so real photos will probably score lower.

## Results

![accuracy per category and prompt regime](results/accuracy_bars.svg)

I used 156 synthetic images, 26 per category, with one question each. The model was
`qwen3-vl:4b-instruct` through Ollama on an Apple M4 (24 GB, no CUDA) at temperature 0. An
answer counts as correct if the first value in it is within a tolerance of the truth (the
rules are in `METHODOLOGY.md`). Every number in this section is tagged, and in CI
`scripts/check_numbers.py` re-derives it from `results/summary.csv` and `results/by_blur.csv`.

### Accuracy per category and prompt regime

| category | describe (verbose) | terse | terse + OCR |
|---|---|---|---|
| dial | <!-- num:acc_verbose_dial -->27<!-- /num -->% | <!-- num:acc_terse_dial -->15<!-- /num -->% | <!-- num:acc_terse_ocr_dial -->23<!-- /num -->% |
| readout | <!-- num:acc_verbose_readout -->12<!-- /num -->% | <!-- num:acc_terse_readout -->12<!-- /num -->% | <!-- num:acc_terse_ocr_readout -->19<!-- /num -->% |
| date | <!-- num:acc_verbose_date -->96<!-- /num -->% | <!-- num:acc_terse_date -->100<!-- /num -->% | <!-- num:acc_terse_ocr_date -->100<!-- /num -->% |
| label_pick | <!-- num:acc_verbose_label_pick -->73<!-- /num -->% | <!-- num:acc_terse_label_pick -->100<!-- /num -->% | <!-- num:acc_terse_ocr_label_pick -->100<!-- /num -->% |
| medication | <!-- num:acc_verbose_medication -->77<!-- /num -->% | <!-- num:acc_terse_medication -->100<!-- /num -->% | <!-- num:acc_terse_ocr_medication -->100<!-- /num -->% |
| button | <!-- num:acc_verbose_button -->92<!-- /num -->% | <!-- num:acc_terse_button -->92<!-- /num -->% | <!-- num:acc_terse_ocr_button -->92<!-- /num -->% |
| all | <!-- num:acc_verbose_all -->63<!-- /num -->% | <!-- num:acc_terse_all -->70<!-- /num -->% | <!-- num:acc_terse_ocr_all -->72<!-- /num -->% |

![accuracy per category](results/accuracy_per_category.png)

Overall the terse prompt did at least as well as the describe prompt (<!-- num:acc_terse_all -->70<!-- /num -->% against
<!-- num:acc_verbose_all -->63<!-- /num -->%). It did a lot better on the two categories that need reading text, where the
long answers tend to wander off. Label pick went from <!-- num:acc_verbose_label_pick -->73<!-- /num -->% to <!-- num:acc_terse_label_pick -->100<!-- /num -->%, and medication
went from <!-- num:acc_verbose_medication -->77<!-- /num -->% to <!-- num:acc_terse_medication -->100<!-- /num -->%. All three prompts read dates and buttons
well. They all read dials and 7-segment displays badly though. The best any prompt got on
dials was <!-- num:acc_verbose_dial -->27<!-- /num -->%, and on readouts <!-- num:acc_terse_ocr_readout -->19<!-- /num -->%. On readouts the model very
often answers "888", which is what it looks like when every segment is lit. So it sees the panel
but can't make out the digits. On dials it either guesses a nearby number or gives up. The terse
prompt says "I can't tell" on <!-- num:cant_terse_dial -->46<!-- /num -->% of dials, and only <!-- num:cant_terse_all -->8<!-- /num -->% overall.

Adding the OCR pass (Apple Vision text through pyobjc) moved the overall number from <!-- num:acc_terse_all -->70<!-- /num -->%
to <!-- num:acc_terse_ocr_all -->72<!-- /num -->%. It helped on dials (<!-- num:acc_terse_dial -->15<!-- /num -->% to <!-- num:acc_terse_ocr_dial -->23<!-- /num -->%),
since the OCR gives the model the tick labels, and on readouts (<!-- num:acc_terse_readout -->12<!-- /num -->% to
<!-- num:acc_terse_ocr_readout -->19<!-- /num -->%). It didn't change dates, labels, medication or buttons, because the
model already reads those fine. With only 26 images per category these differences are small, and
I wouldn't rely on them until I test a bigger set.

### Words before the answer

The describe prompt gives answers that are <!-- num:words_verbose_all -->59.8<!-- /num --> words long on average. The terse
prompt gives <!-- num:words_terse_all -->2.1<!-- /num -->. With the describe prompt, when the right value shows up in the answer at
all, the user hears a median of <!-- num:wb_median_verbose_all -->11.0<!-- /num --> words before it. On dials that median is
<!-- num:wb_median_verbose_dial -->38<!-- /num --> and on readouts it's <!-- num:wb_median_verbose_readout -->15<!-- /num -->. With the terse prompts the median
is <!-- num:wb_median_terse_all -->0<!-- /num -->, so the answer is the first thing the user hears.

![words before answer](results/words_before_answer.png)

### Latency

During the evaluation run the median time per question was <!-- num:lat_median_verbose_all -->18.0<!-- /num --> s for describe, <!-- num:lat_median_terse_all -->13.4<!-- /num --> s
for terse, and <!-- num:lat_median_terse_ocr_all -->12.9<!-- /num --> s for terse with OCR. The terse numbers are much slower than the
model really is. The whole time, another process was running a second 4B model on the same
Ollama server. You can see what that cost in `results/latency_probe.csv`. While the other model
was loaded, Ollama spent about 12 s on prompt evaluation per image, because the image encoder got
pushed off the GPU. Once the other model was unloaded, the same call took 0.5 to 1.4 s. So on an
idle M4 a terse answer comes back in about a second, and in about 13 when it has to share. The
describe prompt also has to generate up to 300 tokens on top of that.

![latency](results/latency.png)

### Blur

I also blurred the images with a Gaussian blur of radius 0, 1.6 and 3.2. The terse prompt got
<!-- num:blur0_terse -->74<!-- /num -->%, <!-- num:blur1_terse -->70<!-- /num -->% and
<!-- num:blur2_terse -->65<!-- /num -->%. With OCR it got <!-- num:blur0_terse_ocr -->78<!-- /num -->%, <!-- num:blur1_terse_ocr -->74<!-- /num -->% and <!-- num:blur2_terse_ocr -->65<!-- /num -->%.
The describe prompt stayed flat at <!-- num:blur0_verbose -->61<!-- /num -->%, <!-- num:blur1_verbose -->61<!-- /num -->% and <!-- num:blur2_verbose -->67<!-- /num -->%.
I think that's because its mistakes come from somewhere else, so blur doesn't matter much for it.

![accuracy vs blur](results/accuracy_vs_blur.png)

### Negative results

* The thinking variant `qwen3-vl:4b` ignores `think: false` in Ollama 0.35, and with a 40 token
  budget it returns an empty answer. With a 2000 token budget it got 10 of 12 probe images right,
  but each one took 9 to 57 s and came with 40 to 315 words of reasoning first
  (`results/thinking_probe.csv`). That's too slow to use here.
* This model at this size just can't read 7-segment displays. It reads the lit shape as "888".
* OCR doesn't fix dials. Knowing the tick labels doesn't tell you where the pointer is.

## What blind users actually asked for

I based the scope of this project on three posts from r/Blind. Here they are as written.

> "AI is so convoluted in it's descriptions that calling someone is waaay faster, E.G, I need to know the exact position of the water level dial of my coffee machine... it'll describe absolutelly everything before saying the water level and usually it will say it wrong."
> https://www.reddit.com/r/Blind/comments/1vyh4dv/

> "1) Privacy - I can't trust Meta... 2) They need always online connection" and "If there were something open source, even if it were bulkier and a little clunkier, I'd be way more comfortable with that."
> https://www.reddit.com/r/Blind/comments/1nqw16e/

> "i'm using qwen3vl-2b model to describe images via nvda script. takes 10s on my laptop with no gpu."
> https://www.reddit.com/r/Blind/comments/1txha0r/

The first post is where the "words before answer" metric comes from. The second is why
everything here runs locally. The third gave me a latency to compare against.

## Limitations

* The test set is synthetic. I drew the dials, 7-segment panels and labels with PIL from a
  seed. That makes the ground truth exact and the set easy to reproduce. But there's no
  glare, no hand in the frame, no perspective and nothing cut off at the edges. Real phone
  photos from blind users will be harder, and that's what I want to try next.
* I only tested one small model (`qwen3-vl:4b`) on one machine, with one run per image at
  temperature 0.
* No blind user has tried this yet. The three quotes above are all the user input I have.
* The scorer takes the first number (or the first "left"/"right") in the answer. If a long
  answer says a wrong number before the right one, it counts as wrong. That's what the user
  hears first, but it also means the describe prompt gets punished for its length twice.
* I looked for a free set of real 7-segment or dial photos with clear labels and a licence I
  could use. I didn't find one in the time I had.

## How to run

You need [Ollama](https://ollama.com) and a Mac for the Apple Vision OCR part. On other
machines the tool still runs, just without OCR.

```
ollama pull qwen3-vl:4b
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -e .

oav ask data/images/dial_000.png "What temperature is the oven dial set to?"
oav ask photo.jpg "what is the best before date" --ocr --time
oav watch "what does the display say"        # webcam, space to ask, q to quit
```

The output is plain text with only the answer on the first line, so a screen reader reads
the answer and then stops.

To regenerate the test set and the results:

```
.venv/bin/python -m oav.generate data          # 156 images, seed 20260101
.venv/bin/python scripts/run_eval.py           # all three regimes, resumable, writes results/raw.csv
.venv/bin/python scripts/summarise.py          # results/summary.csv, results/by_blur.csv
.venv/bin/python scripts/make_figures.py       # results/*.png
.venv/bin/python scripts/check_numbers.py      # fails if a number in this README drifts from the CSVs
.venv/bin/python -m pytest
```

The match rules for each category and the threats to validity are in `METHODOLOGY.md`.
My dated notes are in `notes/LOGBOOK.md`, including the things that didn't work.

## Privacy

Nothing leaves your machine. The image only goes to the Ollama server on localhost and to
the operating system's text recogniser. I don't use API keys, accounts or telemetry. There
are no photos of people or anyone's home in the repo. Every image in `data/` is generated.

## Licence

MIT.
