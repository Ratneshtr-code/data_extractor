# phase2/dataset_builder.py
# -------------------------------------------------------------
# UPSC-AWARE DATASET BUILDER (FINAL PRODUCTION VERSION)
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
import re

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


# -----------------------------------------------------
# INTERNAL HELPERS
# -----------------------------------------------------

def _apply_linebreaks(text: str) -> str:
    """Beautify statement questions with consistent line breaks."""

    if not text:
        return text

    # Normalize "Statement I" / "Statement II"
    text = re.sub(r"Statement\s*[-:]?\s*I\b", "Statement I", text, flags=re.IGNORECASE)
    text = re.sub(r"Statement\s*[-:]?\s*II\b", "Statement II", text, flags=re.IGNORECASE)

    # Add newline after this phrase:
    text = re.sub(
        r"(consider the following statements[:]?)",
        r"\1\n",
        text,
        flags=re.IGNORECASE
    )

    # Newline before Statement I/II
    text = re.sub(r"\s*(Statement I\b)", r"\n\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*(Statement II\b)", r"\n\1", text, flags=re.IGNORECASE)

    # Roman numerals (I., II., III.) we create newlines before them
    text = re.sub(r"(?<!Statement )\s+\b(I|II|III|IV|V)\.", r"\n\1.", text)

    # Newline before numeric lists
    text = re.sub(r"\s*(\d+\.)", r"\n\1", text)

    # Remove extra blank lines
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def _postprocess_question(q_text: str, q_format: str) -> str:
    """Beautify question text based on its format."""

    if q_format == "table":
        q_text = table_formatter.format(q_text)

    if q_format == "statement":
        q_text = _apply_linebreaks(q_text)

    if q_format == "assertion":
        q_text = q_text.replace("Reason (R):", "\nReason (R):")

    return q_text.strip()


def _postprocess_options(options: dict) -> dict:
    """OCR fixes for option text."""

    cleaned = {}

    for key, val in options.items():
        if not val:
            cleaned[key] = ""
            continue

        fixed = ocr_fixer.fix_option(val)
        cleaned[key] = fixed.strip()

    return cleaned


# -----------------------------------------------------
# MAIN PIPELINE
# -----------------------------------------------------

def build_dataset(ocr_files, output_file):

    final_dataset = []

    for file_path in ocr_files:

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
        # STEP 2: PARSE EACH BLOCK USING LLM
        # ---------------------------------------------------------
        for idx, block in enumerate(blocks, start=1):

            print(f"[LLM] Parsing block {idx} for {tag}...")

            raw_json = parse_block(block, f"{tag}_block{idx}")

            # -----------------------------------------------------
            # STEP 3: SANITIZE LLM JSON
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
            # STEP 5: FORMAT CLASSIFICATION (ALWAYS OVERRIDE LLM)
            # -----------------------------------------------------
            llm_format_guess = parsed.get("format", "").strip().lower()
            classified_format = format_classifier.classify(q_text)

            # FINAL — classifier ALWAYS wins
            q_format = classified_format

            # Save debug info
            parsed["llm_format_guess"] = llm_format_guess
            parsed["format"] = q_format

            # -----------------------------------------------------
            # STEP 6: POSTPROCESS QUESTION TEXT
            # -----------------------------------------------------
            q_text = _postprocess_question(q_text, q_format)

            # -----------------------------------------------------
            # STEP 7: POSTPROCESS OPTIONS
            # -----------------------------------------------------
            options = _postprocess_options(options)

            # -----------------------------------------------------
            # STEP 8: ADD METADATA
            # -----------------------------------------------------
            parsed["question"] = q_text
            parsed["options"] = options
            parsed["id"] = make_id(tag, idx)

            parsed.pop("number", None)

            final_dataset.append(parsed)

    # ---------------------------------------------------------
    # STEP 9: SAVE FINAL DATASET JSON
    # ---------------------------------------------------------
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)

    print(f"\n[PHASE 2 COMPLETE] Saved {len(final_dataset)} questions → {output_file}")
