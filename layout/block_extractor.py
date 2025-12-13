import cv2
import numpy as np
import os
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang="en")   # detector + recognizer


def extract_blocks(image_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    img = cv2.imread(image_path)
    if img is None:
        print("[ERROR] cannot load:", image_path)
        return []

    result = ocr.ocr(img, det=True, rec=False)  # only detect boxes
    if not result or not result[0]:
        print("[WARN] No text detected.")
        return []

    boxes = []
    for line in result[0]:
        box = np.array(line[0])
        x1 = box[:,0].min()
        y1 = box[:,1].min()
        x2 = box[:,0].max()
        y2 = box[:,1].max()
        boxes.append([x1, y1, x2, y2])

    # sort top to bottom
    boxes.sort(key=lambda b: (b[1], b[0]))

    images = []
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        crop = img[int(y1):int(y2), int(x1):int(x2)]

        out = os.path.join(output_folder, f"block_{i+1}.png")
        cv2.imwrite(out, crop)
        images.append(out)

    return images
