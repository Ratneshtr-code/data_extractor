# ocr/post_cleaner.py
# -------------------------------------------
# LIGHT OCR NORMALIZATION ONLY
# (No reconstruction here)
# -------------------------------------------

from utils.light_ocr_normalizer import normalize

def clean_ocr_block(text: str) -> str:
    return normalize(text)
