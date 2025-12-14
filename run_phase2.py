# run_phase2.py
# ---------------------------------------------------------
# NEW VERSION — processes ALL PDFs in input_pdfs/
# and generates one JSON per PDF.
# ---------------------------------------------------------

import glob
import os
from phase2.dataset_builder import build_dataset


def run():
    # -----------------------------------------------------
    # STEP 1: Find all PDFs in input_pdfs/
    # -----------------------------------------------------
    pdf_files = sorted(glob.glob("input_pdfs/*.pdf"))

    if not pdf_files:
        print("[ERROR] No PDF files found in input_pdfs/")
        return

    # -----------------------------------------------------
    # STEP 2: For each PDF → process its OCR blocks
    # -----------------------------------------------------
    for pdf_path in pdf_files:
        pdf_name = os.path.basename(pdf_path)           # UPSC_2025.pdf
        base_name = pdf_name.replace(".pdf", "")        # UPSC_2025

        print(f"\n============================")
        print(f"[PHASE 2] Processing PDF :  {pdf_name}")
        print(f"============================")

        # OCR files created in Phase 1: UPSC_2025_p1_c1.txt etc.
        pattern = f"output/ocr_raw/{base_name}_*.txt"
        ocr_files = sorted(glob.glob(pattern))

        if not ocr_files:
            print(f"[WARNING] No OCR files found for: {pdf_name}")
            continue

        # Output JSON path
        output_json = f"output/{base_name}.json"

        # -----------------------------------------------------
        # STEP 3: Build dataset JSON for this specific PDF
        # -----------------------------------------------------
        build_dataset(
            ocr_files=ocr_files,
            output_file=output_json
        )

        print(f"[DONE] Saved  :  {output_json}")


if __name__ == "__main__":
    run()
