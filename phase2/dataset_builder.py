# phase2/dataset_builder.py
# -------------------------------------------------------------
# UPSC DATASET BUILDER — PHASE A (JSON ENRICHMENT)
# -------------------------------------------------------------

import json
import os
import re

from utils.upsc_text_reconstructor import reconstruct_text
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

def _apply_statement_linebreaks(text: str) -> str:
    if not text:
        return text

    # -------------------------------------------------
    # 0. HARD FIX: Split merged "Statement II.n India"
    # -------------------------------------------------
    # Handles:
    #   Statement II.n India
    #   Statement III.n India
    #   Statement I.n India
    #   Statement II In India
    #
    # Converts to:
    #   Statement II.
    #   In India
    # -------------------------------------------------
    text = re.sub(
        r"Statement\s+([IVX]+)\s*[\.\s]*n\s+",
        r"\nStatement \1.\nIn ",
        text,
        flags=re.IGNORECASE
    )

    # -------------------------------------------------
    # 1. Generic OCR fix: broken "In" at line start
    # -------------------------------------------------
    text = re.sub(
        r"(?:(?<=\n)|^)\s*(?:I|l|1)[\.\s]*n\s+([A-Z])",
        r"In \1",
        text
    )

    # -------------------------------------------------
    # 2. Newline after "Consider the following"
    # -------------------------------------------------
    text = re.sub(
        r"(consider the following statements?|consider the following)",
        r"\1\n",
        text,
        flags=re.IGNORECASE
    )

    # -------------------------------------------------
    # 3. Normalize remaining Statement headers
    # -------------------------------------------------
    def normalize_statement(match):
        roman = match.group(1)
        return f"\nStatement {roman}."

    text = re.sub(
        r"Statement\s*\n*\s*(I|II|III|IV|V|VI|VII|VIII|IX|X)\b(?!\.)",
        normalize_statement,
        text,
        flags=re.IGNORECASE
    )

    # -------------------------------------------------
    # 4. Roman bullets (ONLY if NOT part of Statement)
    # -------------------------------------------------
    text = re.sub(
        r"(?<!Statement )(?<!\n)\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\.",
        r"\n\1.",
        text
    )

    # -------------------------------------------------
    # 5. Numeric bullets
    #    Only treat 1- or 2-digit numbers as bullets to
    #    avoid turning years like "1961." into a new line.
    # -------------------------------------------------
    text = re.sub(
        r"(?<!\n)(\b\d{1,2}\.)",
        r"\n\1",
        text
    )

    # -------------------------------------------------
    # 6. Cleanup
    # -------------------------------------------------
    text = re.sub(r"\n{2,}", "\n\n", text)

    return text.strip()




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
    # Only match 1-2 digit numeric bullets so years like "1961." are not treated as bullets
    text = re.sub(r"(?m)(^|\n)\s*(\d{1,2}\.)", r"\n\2", text)

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
            raw_q = parsed.get("question", "").strip()
            options = normalize_options(parsed.get("options", {}))

            # FORMAT DETECTION MUST HAPPEN FIRST
            q_format = format_classifier.classify(raw_q)

            # FORMAT-AWARE RECONSTRUCTION
            if q_format == "statement":
                q_text = reconstruct_text(raw_q)
                q_text = _apply_statement_linebreaks(q_text)

            elif q_format in ("match", "table", "assertion"):
                q_text = reconstruct_text(raw_q)

            else:
                q_text = raw_q

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
