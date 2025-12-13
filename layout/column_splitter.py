# layout/column_splitter.py

import cv2
import os

def split_into_columns(image_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot load {image_path}")

    h, w = img.shape[:2]

    # --- FINAL SOLID APPROACH ---
    # For UPSC/PSC/SSC/Banking PDFs the scan geometry places
    # the two columns almost exactly at mid-width.
    #
    # We simply cut the page at 49%/51% ± a small margin.

    mid = int(w * 0.50)     # 50% split point
    margin = int(w * 0.02)  # 2% margin to avoid cutting text

    left_end = max(0, mid - margin)
    right_start = min(w, mid + margin)

    left = img[:, :left_end]
    right = img[:, right_start:]

    left_path = os.path.join(output_folder, "left.png")
    right_path = os.path.join(output_folder, "right.png")

    cv2.imwrite(left_path, left)
    cv2.imwrite(right_path, right)

    print(f"[COLUMN] Split at x={mid}, saved left/right columns")
    return [left_path, right_path]
