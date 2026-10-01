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
