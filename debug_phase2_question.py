# test_phase2_single.py

from phase2.dataset_builder import build_dataset

# 👇 CHANGE THIS TO THE EXACT FILE YOU WANT TO TEST
ocr_files = [
    "output/ocr_raw/UPSC_2025_p1_c2.txt"
]

output_file = "output/TEST_UPSC_2025_p1_c2.json"

build_dataset(
    ocr_files=ocr_files,
    output_file=output_file
)
