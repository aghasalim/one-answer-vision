# Logbook

## 2026-10-01

Started. The idea comes from three r/Blind threads (quoted in the README): assistants
describe everything before answering, they need a connection, and people would take a
clunkier open tool that runs on their own machine. So: one image, one question, one short
answer, local model, and measure whether the short answer is also a correct answer.

Set up a venv on Python 3.14. Ollama had no vision model, pulling `qwen3-vl:4b` (3.3 GB)
at under 1 MB/s because another job is pulling at the same time. Built the rest while
waiting.

Synthetic set: 6 categories x 26 = 156 images, 8 MB. Checked a contact sheet by eye: the
dials, 7-segment panels and labels are readable at blur 0 and 1, blur 2 is hard for me too.
That is intended, it is the "accuracy vs blur" axis.

No tesseract on this machine, but pyobjc gives Apple Vision. Tested on five images: it reads
the date label and the pharmacy label perfectly, reads button names, reads dial tick labels
(useless for the pointer, as expected) and finds nothing on the 7-segment panel except the
word OVEN. So OCR should help on date, medication and button, and do nothing on dial and
readout. We will see.

Looked for a real free 7-segment or dial dataset to add as a real subset. Found papers
mentioning small sets (SSDI, 257 images; a 7Seg set of 189 web images) but no download with
a clear licence and labels I could pull in quickly. Skipped, noted in the README.

Tests pass (48) with Ollama mocked. CI runs tests plus the README number check only, no model.

### Thinking variant failure

`ollama pull qwen3-vl:4b` gives the thinking variant. With Ollama 0.35 it ignores
`think: false` on both `/api/generate` and `/api/chat`, and `/no_think` in the prompt does
nothing either. With my 40 token budget every answer came back empty: the whole budget went
into the thinking field. The first CLI call printed a blank line after 19 seconds.

Probed it with a 2000 token budget on 12 images (`scripts/thinking_probe.py`,
`results/thinking_probe.csv`): 10 of 12 right, but 9 to 57 seconds per question and 40 to
315 words of reasoning before the answer, which is the opposite of what the project is for.
Both 7-segment readouts came back as "888". Switched to `qwen3-vl:4b-instruct` (another
3.3 GB), which answers the terse prompt in about a second once loaded. The default model
in `oav/vlm.py` is now the instruct tag.

### Full run

468 calls (156 images x 3 regimes) in 6989 s, resumable script, no crashes. Overall
accuracy: describe 62%, terse 68%, terse with OCR 71%. Terse wins clearly on label pick and
medication, loses a little on dials, ties on dates and buttons. Dials and readouts are bad
everywhere. On the 7-segment panels the model answers "888" again and again, so the digit
rendering is being seen as a block rather than as digits. I expected the dial to be the hard
one, not the readout.

Words before the answer: median 12 in the describe regime, 0 in the terse ones. That is the
figure the first Reddit quote is about.

Latency surprise: the terse regime sat at 13 s per call with almost no variance, while the
smoke test before the run took 0.9 s. Ollama's own timing fields explain it
(`scripts/latency_probe.py`): with another 4B model loaded by a different job, prompt
evaluation for one 640 px image took 12 s; halfway through the probe the other model was
evicted and the same call dropped to 0.5 to 1.4 s. So the eval run latencies are a
contended measurement and the README says so. I did not rerun the whole set on an idle
machine because the machine was not idle.

Blur: terse goes 72, 69, 63% from no blur to radius 3.2. OCR helps at blur 0 and 1 and not
at 2, which is where Apple Vision starts misreading too.

What I would do next: real phone photos from blind users, a bigger set so the OCR deltas
mean something, a crop-and-zoom step for readouts, and try a 7-segment specific reader
before the VLM.

2026-10-10. Found a scorer bug: `parse_date("2026-03")` returned year 2003, month 26,
because the `MM/YY` pattern matched "26-03" inside the ISO year-month. Seven date answers
that were right (2026-12, 2027-04, 2027-12) were scored wrong. Added a year-month pattern
before it, tests for it, and rescored `raw.csv` from the stored answers; no other row
changed. Terse date goes 88 to 100%, terse overall 68 to 70%.

2026-10-10, later. Second scorer bug, in buttons this time. For a truth of "middle centre"
any answer with "middle" in it passed the column check, so "middle left" counted as right.
"middle" now only stands for the centre column when the answer names no other column.
Rescoring `raw.csv` from the stored answers changed no `correct` value, because none of the
model's button answers hit that case. It did change `words_before` on the nine date rows from
the morning's fix, which I had rescored for `correct` but not for words before the answer.
With those filled in, the describe median goes from 12 to 11 words; the terse medians stay 0.
