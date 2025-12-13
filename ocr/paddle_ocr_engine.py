# ocr/paddle_ocr_engine.py

from paddleocr import PaddleOCR

class OCREngine:
    def __init__(self):
        print("[OCR] Initializing PaddleOCR...")

        # use_angle_cls is now internal — new API uses default models
        self.ocr = PaddleOCR(lang="en")

    def extract_text(self, image_path):
        result = self.ocr.ocr(image_path)
        lines = []

        if not result or not result[0]:
            return ""

        # result[0] is the list of detections
        for box, (text, conf) in result[0]:
            lines.append(text)

        return "\n".join(lines)

