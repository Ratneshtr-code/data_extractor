# phase2/dataset_builder.py

import json
from phase2.parser_groq import parse_question_block
from phase2.formatter import clean_ocr_text
from phase2.question_extractor import split_into_questions
from phase2.json_sanitizer import sanitize_and_load


def build_dataset(ocr_files, output_file):
    dataset = []
    q_counter = 1

    for file_path in ocr_files:

        # -----------------------------
        # 1. Load OCR raw text
        # -----------------------------
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # -----------------------------
        # 2. Split into question blocks
        # -----------------------------
        question_blocks = split_into_questions(raw_text)

        # -----------------------------
        # 3. Clean block formatting
        # -----------------------------
        cleaned_blocks = []
        for qb in question_blocks:
            cleaned_blocks.extend(clean_ocr_text(qb))

        # -----------------------------
        # 4. Parse each question using Groq
        # -----------------------------
        for cb in cleaned_blocks:

            raw_response = parse_question_block(cb, q_counter)

            parsed_json = sanitize_and_load(raw_response, q_counter)

            dataset.append({
                "id": f"q_{q_counter}",
                "raw": cb,
                "parsed": parsed_json
            })

            q_counter += 1

    # -----------------------------
    # 5. Save final dataset
    # -----------------------------
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"[DATASET] Saved {len(dataset)} questions → {output_file}")
