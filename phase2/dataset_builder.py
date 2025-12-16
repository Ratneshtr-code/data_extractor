# phase2/dataset_builder.py
# -------------------------------------------------------------
# UPSC DATASET BUILDER — PHASE A (JSON ENRICHMENT)
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
# HELPERS
# -----------------------------------------------------

def _apply_linebreaks(text: str) -> str:
    if not text:
        return text

    text = re.sub(
        r"(consider the following statements[:]?)",
        r"\1\n",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"Statement\s*[-:]?\s*I\b", "Statement I", text, flags=re.IGNORECASE)
    text = re.sub(r"Statement\s*[-:]?\s*II\b", "Statement II", text, flags=re.IGNORECASE)

    text = re.sub(r"(?<!Statement )\s+\b(I|II|III|IV|V)\.", r"\n\1.", text)
    text = re.sub(r"\s*(\d+\.)", r"\n\1", text)

    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def _postprocess_question(q_text: str, q_format: str) -> str:
    if q_format == "table":
        q_text = table_formatter.format(q_text)

    if q_format == "statement":
        q_text = _apply_linebreaks(q_text)

    if q_format == "assertion":
        q_text = q_text.replace("Reason (R):", "\nReason (R):")

    return q_text.strip()


def _postprocess_options(options: dict) -> dict:
    cleaned = {}
    for key, val in options.items():
        if not val:
            cleaned[key] = ""
            continue
        cleaned[key] = ocr_fixer.fix_option(val).strip()
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

        print(f"\n[SEGMENT] Processing column → {tag}")
        blocks = segment_column(col_text, tag)

        if not blocks:
            continue

        for idx, block in enumerate(blocks, start=1):

            print(f"[LLM] Parsing block {idx} for {tag}")
            raw_json = parse_block(block, f"{tag}_block{idx}")
            parsed = sanitize_and_load(raw_json)

            if not isinstance(parsed, dict):
                continue

            # -------------------------------
            # BASIC FIELDS
            # -------------------------------
            q_text = parsed.get("question", "").strip()
            options = normalize_options(parsed.get("options", {}))

            # -------------------------------
            # FORMAT — ALWAYS CLASSIFIER WINS
            # -------------------------------
            q_format = format_classifier.classify(q_text)

            # -------------------------------
            # POSTPROCESS TEXT
            # -------------------------------
            q_text = _postprocess_question(q_text, q_format)
            options = _postprocess_options(options)

            # -------------------------------
            # ENSURE REQUIRED TAGS EXIST
            # -------------------------------
            parsed.setdefault("subject", None)
            parsed.setdefault("topic", None)
            parsed.setdefault("sub_topic", None)
            parsed.setdefault("keywords", [])

            parsed.setdefault("correct_answer", None)
            parsed.setdefault("is_multi_correct", False)

            # -------------------------------
            # FINAL ASSIGNMENTS
            # -------------------------------
            parsed["question"] = q_text
            parsed["options"] = options
            parsed["format"] = q_format
            parsed["id"] = make_id(tag, idx)

            parsed.pop("number", None)

            final_dataset.append(parsed)

    # -------------------------------------------------
    # SAVE JSON
    # -------------------------------------------------
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)

    print(f"\n[PHASE A COMPLETE] Saved {len(final_dataset)} questions → {output_file}")
