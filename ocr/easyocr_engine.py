# ocr/easyocr_engine.py

import easyocr

class OCREngine:
    def __init__(self):
        print("[OCR] Initializing EasyOCR")
        self.reader = easyocr.Reader(['en'], gpu=False)

    def extract_text(self, image_path):
        result = self.reader.readtext(image_path, detail=0)
        return "\n".join(result)
