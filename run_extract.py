# run_extract.py
# ---------------------------------------------------------
# NEW VERSION — processes ALL PDFs in input_pdfs/
# and produces OCR output for each (without wiping others).
# ---------------------------------------------------------

import os
import glob
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

def clean_output_dirs():
    folders = [
        "output/images",
        "output/columns",
        "output/ocr_raw",
        "output/ocr_clean",
        "logs/groq_segment_raw"
    ]

    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)

    # recreate directories
    os.makedirs("output/images", exist_ok=True)
    os.makedirs("output/columns", exist_ok=True)
    os.makedirs("output/ocr_raw", exist_ok=True)
    os.makedirs("output/ocr_clean", exist_ok=True)
    os.makedirs("logs/groq_segment_raw", exist_ok=True)

def parse_filename(pdf_name):
    """
    EXAM_YEAR.pdf
    Example: UPSC_2025.pdf → exam="UPSC", year=2025
    """
    base = pdf_name.replace(".pdf", "")
    parts = base.split("_")

    # Handle PDFs without year (e.g., test2.pdf → exam="test2", year=None)
    if len(parts) == 2 and parts[1].isdigit():
        exam = parts[0]
        year = int(parts[1])
    else:
        exam = base
        year = None

    return exam, year


def process_pdf(pdf_name):
    print(f"\n==============================")
    print(f"[PHASE 1] Processing → {pdf_name}")
    print("==============================")

    exam, year = parse_filename(pdf_name)

    ensure_dirs()

    pdf_path = f"input_pdfs/{pdf_name}"
    imgs = pdf_to_images(pdf_path, "output/images", dpi=600)

    ocr = OCREngine()

    for page_idx, img in enumerate(imgs, start=1):

        col_folder = f"output/columns/{exam}_p{page_idx}"
        os.makedirs(col_folder, exist_ok=True)

        columns = split_into_columns(img, col_folder)

        for col_idx, col_img in enumerate(columns, start=1):

            print(f"[OCR] {pdf_name} → Page {page_idx} Column {col_idx}")

            raw = ocr.extract_text(col_img)
            clean = clean_ocr_block(raw)

            # meta_tag should include exam + year if available
            if year:
                meta_tag = f"{exam}_{year}_p{page_idx}_c{col_idx}"
            else:
                meta_tag = f"{exam}_p{page_idx}_c{col_idx}"

            with open(f"output/ocr_raw/{meta_tag}.txt", "w", encoding="utf-8") as f:
                f.write(raw)

            with open(f"output/ocr_clean/{meta_tag}.txt", "w", encoding="utf-8") as f:
                f.write(clean)

    print(f"[PHASE 1 COMPLETE] OCR generated for {pdf_name}")


def run_all_pdfs():
    # CLEAN OUTPUT FIRST
    clean_output_dirs()

    pdf_files = sorted(glob.glob("input_pdfs/*.pdf"))

    if not pdf_files:
        print("[ERROR] No PDF files found in input_pdfs/")
        return

    for pdf in pdf_files:
        pdf_name = os.path.basename(pdf)
        process_pdf(pdf_name)


if __name__ == "__main__":
    run_all_pdfs()
