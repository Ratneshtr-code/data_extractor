# run_extract.py

import os
import shutil
from utils.pdf_converter import pdf_to_images
from layout.column_splitter import split_into_columns
from ocr.easyocr_engine import OCREngine
from ocr.post_cleaner import clean_ocr_block


def ensure_dirs():
    os.makedirs("output/images", exist_ok=True)
    os.makedirs("output/columns", exist_ok=True)
    os.makedirs("output/ocr_raw", exist_ok=True)
    os.makedirs("output/ocr_clean", exist_ok=True)


def clean_output():
    if os.path.exists("output"):
        shutil.rmtree("output")


def parse_filename(pdf_name):
    """
    EXAM_YEAR.pdf
    Example: UPSC_2025.pdf → exam="UPSC", year=2025
    """
    base = pdf_name.replace(".pdf", "")
    exam, year = base.split("_")
    return exam, int(year)


def run(pdf_name):
    clean_output()
    ensure_dirs()

    exam, year = parse_filename(pdf_name)

    pdf_path = f"input_pdfs/{pdf_name}"
    imgs = pdf_to_images(pdf_path, "output/images", dpi=600)

    ocr = OCREngine()

    for page_idx, img in enumerate(imgs, start=1):

        col_folder = f"output/columns/page_{page_idx}"
        columns = split_into_columns(img, col_folder)

        for col_idx, col_img in enumerate(columns, start=1):

            print(f"[OCR] Page {page_idx} Column {col_idx}")

            raw = ocr.extract_text(col_img)
            clean = clean_ocr_block(raw)

            meta_tag = f"{exam}_{year}_p{page_idx}_c{col_idx}"

            with open(f"output/ocr_raw/{meta_tag}.txt", "w", encoding="utf-8") as f:
                f.write(raw)

            with open(f"output/ocr_clean/{meta_tag}.txt", "w", encoding="utf-8") as f:
                f.write(clean)

    print("\n[PHASE 1 COMPLETE] Clean OCR saved.")


if __name__ == "__main__":
    run("UPSC_2025.pdf")
