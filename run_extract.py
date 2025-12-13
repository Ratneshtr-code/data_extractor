# run_extract.py

import os
import shutil

from utils.pdf_converter import pdf_to_images
from layout.column_splitter import split_into_columns
from ocr.paddle_ocr_engine import OCREngine

def ensure_output_dirs():
    os.makedirs("output/images", exist_ok=True)
    os.makedirs("output/columns", exist_ok=True)
    os.makedirs("output/ocr_raw", exist_ok=True)

def clean_output():
    if os.path.exists("output"):
        shutil.rmtree("output")

def run(pdf_name):
    clean_output()
    ensure_output_dirs()

    pdf_path = f"input_pdfs/{pdf_name}"
    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF not found: {pdf_path}")
        return

    img_paths = pdf_to_images(pdf_path, "output/images", dpi=600)
    ocr_engine = OCREngine()

    for page_idx, img in enumerate(img_paths):
        col_folder = f"output/columns/page_{page_idx+1}"
        col_paths = split_into_columns(img, col_folder)

        for col_idx, col_img in enumerate(col_paths):
            print(f"[OCR] Page {page_idx+1}, Column {col_idx+1}")
            text = ocr_engine.extract_text(col_img)

            out_path = f"output/ocr_raw/page_{page_idx+1}_col_{col_idx+1}.txt"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)

    print("\n[INFO] Phase-1 complete with improved OCR & column splitting.")


if __name__ == "__main__":
    run("test.pdf")   # Change this to your filename
