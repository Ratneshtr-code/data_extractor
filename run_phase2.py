# run_phase2.py

import glob
from phase2.dataset_builder import build_dataset

def run():
    # Load OCR text files from phase1 output
    ocr_files = sorted(glob.glob("output/ocr_raw/*.txt"))

    if not ocr_files:
        print("[ERROR] No OCR files found in output/ocr_raw/")
        return

    build_dataset(
        ocr_files=ocr_files,
        output_file="output/final_dataset.json"
    )

if __name__ == "__main__":
    run()
