"""OCR pre-pass. Apple Vision through pyobjc when available, else tesseract, else nothing."""
import shutil
import subprocess


def backend() -> str | None:
    try:
        import Vision  # noqa: F401
        return "apple_vision"
    except ImportError:
        pass
    if shutil.which("tesseract"):
        return "tesseract"
    return None


def _apple_vision(path: str) -> str:
    import Vision
    from Foundation import NSURL
    url = NSURL.fileURLWithPath_(path)
    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    ok, err = handler.performRequests_error_([req], None)
    if not ok:
        return ""
    lines = []
    for obs in req.results() or []:
        cand = obs.topCandidates_(1)
        if cand:
            lines.append(str(cand[0].string()))
    return "\n".join(lines)


def _tesseract(path: str) -> str:
    out = subprocess.run(["tesseract", path, "-", "--psm", "6"], capture_output=True, text=True)
    return out.stdout.strip()


def read_text(path: str) -> str:
    b = backend()
    if b == "apple_vision":
        return _apple_vision(path)
    if b == "tesseract":
        return _tesseract(path)
    return ""
