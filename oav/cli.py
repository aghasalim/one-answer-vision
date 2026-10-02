"""oav ask IMAGE QUESTION   |   oav watch QUESTION"""
import argparse
import os
import sys
import tempfile

from .ocr import backend
from .vlm import DEFAULT_MODEL, ask


def main(argv=None):
    p = argparse.ArgumentParser(prog="oav", description="One image, one question, one short answer. Offline.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask", help="ask a question about an image file")
    a.add_argument("image")
    a.add_argument("question")
    w = sub.add_parser("watch", help="webcam: press space to take a frame and ask, q to quit")
    w.add_argument("question")
    w.add_argument("--camera", type=int, default=0)
    for s in (a, w):
        s.add_argument("--model", default=DEFAULT_MODEL)
        s.add_argument("--regime", default="terse", choices=("verbose", "terse", "terse_ocr"))
        s.add_argument("--ocr", action="store_true", help="shortcut for --regime terse_ocr")
        s.add_argument("--time", action="store_true", help="print latency on a second line")
    args = p.parse_args(argv)
    if args.ocr:
        args.regime = "terse_ocr"
    if args.regime == "terse_ocr" and backend() is None:
        print("No OCR backend (pyobjc Vision or tesseract) found, running without OCR.", file=sys.stderr)
        args.regime = "terse"

    def one(path):
        r = ask(path, args.question, args.regime, args.model)
        # plain text, answer first, nothing else: this is what a screen reader will speak
        print(r["answer"])
        if args.time:
            print(f"{r['latency_s']:.1f} seconds")
        sys.stdout.flush()

    if args.cmd == "ask":
        one(args.image)
        return
    import cv2
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        sys.exit("camera not available")
    print("space = ask, q = quit", file=sys.stderr)
    while True:
        ok, frame = cap.read()
        if not ok:
            sys.exit("could not read frame")
        cv2.imshow("oav", frame)
        k = cv2.waitKey(30) & 0xFF
        if k == ord("q"):
            break
        if k == ord(" "):
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                cv2.imwrite(f.name, frame)
            one(f.name)
            os.unlink(f.name)
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
