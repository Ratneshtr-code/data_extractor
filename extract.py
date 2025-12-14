# run_all.py
# ---------------------------------------------------------
# RUNS THE FULL DATASET PIPELINE:
#   1. PHASE 1 → OCR extraction for ALL PDFs
#   2. PHASE 2 → LLM parsing & JSON dataset generation
#
# REQUIREMENTS:
#   run_extract.py must define run_all_pdfs()
#   run_phase2.py must define run()
# ---------------------------------------------------------

import run_extract
import run_phase2


def main():
    print("\n===========================================")
    print("        UPSC DATA EXTRACTOR — FULL RUN")
    print("===========================================\n")

    # -----------------------
    # PHASE 1 — OCR extraction
    # -----------------------
    print("\n-------------------------------------------")
    print("PHASE 1 — Running OCR extraction for all PDFs")
    print("-------------------------------------------\n")

    run_extract.run_all_pdfs()

    # -----------------------
    # PHASE 2 — LLM parsing
    # -----------------------
    print("\n-------------------------------------------")
    print("PHASE 2 — Running dataset builder for all PDFs")
    print("-------------------------------------------\n")

    run_phase2.run()

    print("\n===========================================")
    print("✔ FULL PIPELINE COMPLETE — READY FOR REVIEW")
    print("===========================================\n")


if __name__ == "__main__":
    main()
