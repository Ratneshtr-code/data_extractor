# utils/table_handler.py
# ------------------------------------------------------
# Table Handler — Flatten OCR Table Rows
# ------------------------------------------------------
# OCR often breaks table formatting so we flatten rows
# into readable text lines.
#
# Input example (OCR):
#   "Directorate | Enforcement | MHA"
#   "DRI | Customs Act | MoF"
#
# Output:
#   [
#     "Directorate – Enforcement – MHA",
#     "DRI – Customs Act – MoF"
#   ]
#
# Does NOT paraphrase or change wording.
# ------------------------------------------------------

import re


def flatten_table_rows(rows):
    """
    Input:  list of OCR lines containing '|'
    Output: list of flattened readable rows
    """

    flattened = []
    for row in rows:
        # Split columns using '|'
        parts = [p.strip() for p in row.split("|") if p.strip()]

        if not parts:
            continue

        # Join with en-dash — preserves meaning without paraphrasing
        flattened.append(" – ".join(parts))

    return flattened
