# ocr/paddle_ocr_engine.py

from paddleocr import PaddleOCR
from ocr.post_cleaner import clean_ocr_block

class OCREngine:
    def __init__(self):
        print("[OCR] Initializing PaddleOCR...")
        self.ocr = PaddleOCR(lang="en")

    def extract_text(self, image_path):
        result = self.ocr.ocr(image_path)
        lines = []

        if not result or not result[0]:
            return ""

        for box, (text, conf) in result[0]:
            lines.append(text)

        raw_text = "\n".join(lines)

        # USE STRONG CLEANER
        return clean_ocr_block(raw_text)
