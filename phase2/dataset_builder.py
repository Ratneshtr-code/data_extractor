# phase2/dataset_builder.py
# -------------------------------------------------------------
# NEW UPSC-AWARE DATASET BUILDER (FINAL PRODUCTION VERSION)
# -------------------------------------------------------------
# Pipeline:
#   1. Reads cleaned OCR text (Phase 1 output)
#   2. LLM Column Segmentation → question blocks
#   3. Per-block LLM parsing → structured JSON
#   4. Sanitize JSON
#   5. Normalize options (A/B/C/D/E)
#   6. Classify format (statement, table, match, assertion, paragraph, single)
#   7. Beautify tables
#   8. Fix OCR glitches ("ll the four" → "All the four")
#   9. Insert UI-friendly line breaks
#  10. Assign IDs
#  11. Save final dataset JSON
# -------------------------------------------------------------

import json
import os

from phase2.segmenter_groq import segment_column
from phase2.block_parser import parse_block
from phase2.json_sanitizer import sanitize_and_load
from phase2.option_normalizer import normalize_options
from phase2.format_classifier import FormatClassifier
from phase2.table_formatter import TableFormatter
from phase2.ocr_fixer import SafeOCRFixer
from phase2.id_gen import make_id


format_classifier = FormatClassifier()
table_formatter = TableFormatter()
ocr_fixer = SafeOCRFixer()


def _apply_linebreaks(text: str) -> str:
    """
    Insert clean UI-friendly line breaks for statement-format questions.
    Does NOT change wording.
    """
    if not text:
        return text

    # Create newline before Roman numerals
    text = text.replace(" I.", "\nI.")
    text = text.replace(" II.", "\nII.")
    text = text.replace(" III.", "\nIII.")
    text = text.replace(" IV.", "\nIV.")
    text = text.replace(" V.", "\nV.")

    # Ensure question ends cleanly
    return text.strip()


def _postprocess_question(q_text: str, q_format: str) -> str:
    """
    Applies formatting transformations to question text.
    """

    # Beautify tables
    if q_format == "table":
        q_text = table_formatter.format(q_text)

    # Insert line breaks for statements
    if q_format == "statement":
        q_text = _apply_linebreaks(q_text)

    # Insert line breaks for assertion–reason
    if q_format == "assertion":
        q_text = q_text.replace("Reason (R):", "\nReason (R):")

    return q_text.strip()


def _postprocess_options(options: dict) -> dict:
    """
    Normalize and fix option OCR glitches.
    """

    cleaned = {}

    for key, val in options.items():
        if not val:
            cleaned[key] = ""
            continue

        # Fix OCR glitches safely
        fixed = ocr_fixer.fix_option(val)

        cleaned[key] = fixed.strip()

    return cleaned


def build_dataset(ocr_files, output_file):

    final_dataset = []

    for file_path in ocr_files:

        # Produce clean tag: UPSC_2025_p1_c1
        tag = os.path.basename(file_path).replace(".txt", "")

        with open(file_path, "r", encoding="utf-8") as f:
            col_text = f.read().strip()

        # ---------------------------------------------------------
        # STEP 1: SEGMENT COLUMN USING LLM
        # ---------------------------------------------------------
        print(f"\n[SEGMENT] Processing column → {tag}")
        blocks = segment_column(col_text, tag)

        if not blocks:
            print(f"[WARNING] No blocks detected in: {file_path}")
            continue

        # ---------------------------------------------------------
        # STEP 2: PARSE EACH BLOCK USING BLOCK PARSER LLM
        # ---------------------------------------------------------
        for idx, block in enumerate(blocks, start=1):

            print(f"[LLM] Parsing block {idx} for {tag}...")

            raw_json = parse_block(block, f"{tag}_block{idx}")

            # -----------------------------------------------------
            # STEP 3: CLEAN JSON OUTPUT
            # -----------------------------------------------------
            parsed = sanitize_and_load(raw_json)

            if not isinstance(parsed, dict):
                print(f"[ERROR] Block {idx} → Invalid LLM output → Skipping")
                continue

            q_text = parsed.get("question", "").strip()
            options = parsed.get("options", {})

            # -----------------------------------------------------
            # STEP 4: NORMALIZE OPTIONS
            # -----------------------------------------------------
            options = normalize_options(options)

            # -----------------------------------------------------
            # STEP 5: CLASSIFY QUESTION FORMAT
            # -----------------------------------------------------
            q_format = parsed.get("format")
            if not q_format:
                q_format = format_classifier.classify(q_text)

            # -----------------------------------------------------
            # STEP 6: POSTPROCESS QUESTION TEXT
            # -----------------------------------------------------
            q_text = _postprocess_question(q_text, q_format)

            # -----------------------------------------------------
            # STEP 7: POSTPROCESS OPTIONS (OCR FIXES)
            # -----------------------------------------------------
            options = _postprocess_options(options)

            # -----------------------------------------------------
            # STEP 8: ADD METADATA
            # -----------------------------------------------------
            parsed["question"] = q_text
            parsed["options"] = options
            parsed["format"] = q_format
            parsed["id"] = make_id(tag, idx)

            # Remove question number (never needed)
            parsed.pop("number", None)

            final_dataset.append(parsed)

    # ---------------------------------------------------------
    # STEP 9: SAVE FINAL DATASET JSON
    # ---------------------------------------------------------
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)

    print(f"\n[PHASE 2 COMPLETE] Saved {len(final_dataset)} questions → {output_file}")
