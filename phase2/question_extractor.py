# phase2/question_extractor.py

import re

def split_into_questions(column_text):
    """
    Input: raw OCR text from one column
    Output: list of block strings; each block contains one full question
    """

    # Normalize spacing
    text = column_text.replace("\r", "")

    # Split using question numbers (1., 2., 12., etc.)
    parts = re.split(r"(?m)(?=^\d+\.)", text)

    blocks = [p.strip() for p in parts if p.strip()]

    return blocks
