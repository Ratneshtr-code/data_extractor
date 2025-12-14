# phase2/dataset_builder.py
# -------------------------------------------------------------
# NEW DATASET BUILDER (UPSCAware)
# -------------------------------------------------------------
# This module replaces full-column parsing.
# It now:
#   1. Loads OCR-cleaned column text
#   2. Uses UPSCQuestionBlockDetector →  question blocks
#   3. Calls BlockParser per block (LLM)
#   4. Sanitizes JSON
#   5. Normalizes options
#   6. Classifies question format
#   7. Assigns stable IDs
#   8. Produces final dataset list
# -------------------------------------------------------------

import json
import os
import glob

from utils.upsc_question_block_detector import detect_question_blocks
from phase2.block_parser import parse_block
from phase2.json_sanitizer import sanitize_and_load
from phase2.option_normalizer import normalize_options
from phase2.format_classifier import classify_format
from phase2.id_gen import make_id
from phase2.segmenter_groq import segment_column


def build_dataset(ocr_files, output_file):

    final_dataset = []

    for file_path in ocr_files:

        # Extract tag like "UPSC_2025_p1_c1"
        tag = os.path.basename(file_path).replace(".txt", "")

        with open(file_path, "r", encoding="utf-8") as f:
            col_text = f.read().strip()

        # ---------------------------------------------------------
        # STEP 1: Detect individual UPSC question blocks
        # ---------------------------------------------------------
        blocks = segment_column(col_text, tag)

        if not blocks:
            print(f"[WARNING] No blocks detected in: {file_path}")
            continue

        # ---------------------------------------------------------
        # STEP 2: Parse each block with Groq LLM
        # ---------------------------------------------------------
        for idx, block in enumerate(blocks, start=1):

            print(f"[LLM] Parsing block {idx} for {tag}...")

            raw_json = parse_block(block, f"{tag}_block{idx}")

            # -----------------------------------------------------
            # STEP 3: Sanitize the raw JSON output
            # -----------------------------------------------------
            parsed = sanitize_and_load(raw_json)

            if not isinstance(parsed, dict):
                print(f"[ERROR] Block {idx} → Invalid LLM output → Skipping")
                continue

            # -----------------------------------------------------
            # STEP 4: Normalize options
            # -----------------------------------------------------
            if "options" in parsed and parsed["options"]:
                parsed["options"] = normalize_options(parsed["options"])
            else:
                parsed["options"] = {}

            # -----------------------------------------------------
            # STEP 5: Classify question format (fallback)
            # -----------------------------------------------------
            if not parsed.get("format"):
                parsed["format"] = classify_format(parsed.get("question", ""))

            # -----------------------------------------------------
            # STEP 6: Add metadata
            # -----------------------------------------------------
            parsed["id"] = make_id(tag, idx)

            # user asked to omit question number → ensure removed
            parsed.pop("number", None)

            final_dataset.append(parsed)

    # ---------------------------------------------------------
    # STEP 7: Save final dataset JSON
    # ---------------------------------------------------------
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)

    print(f"[PHASE 2 COMPLETE] Saved {len(final_dataset)} questions → {output_file}")
