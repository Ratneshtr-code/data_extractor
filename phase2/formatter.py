# phase2/formatter.py

import re

def clean_ocr_text(raw_text):
    """Normalize OCR noise and join broken lines safely."""

    # remove empty lines
    lines = [ln.strip() for ln in raw_text.split("\n") if ln.strip()]

    # join lines that do NOT start with option labels or question numbers
    cleaned = []
    buf = ""

    for ln in lines:

        # If line starts with question number -> start new block
        if re.match(r"^\d+\.", ln):
            if buf:
                cleaned.append(buf.strip())
            buf = ln
            continue

        # If line starts with option label (A/B/C/D)
        if re.match(r"^[A-D]\)", ln):
            buf += "\n" + ln
            continue

        # Otherwise: continuation line
        buf += " " + ln

    if buf:
        cleaned.append(buf.strip())

    return cleaned
