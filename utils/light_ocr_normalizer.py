# utils/light_ocr_normalizer.py
# -------------------------------------------
# Minimal OCR cleanup.
# ❌ NO merging
# ❌ NO restructuring
# ✔ Only removes garbage characters
# -------------------------------------------

import re

def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\u00A0", " ").replace("\u200B", "")
    text = re.sub(r"[•●■▪▫]", "", text)

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    return "\n".join(lines)
