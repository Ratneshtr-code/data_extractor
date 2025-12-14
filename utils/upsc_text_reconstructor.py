# utils/upsc_text_reconstructor.py
# ---------------------------------------------------------
# UPSC-Aware Text Reconstruction Engine
# ---------------------------------------------------------
# This module replaces the old post_cleaner.py logic.
# It does NOT modify wording — only fixes STRUCTURE.
# ---------------------------------------------------------

import re
from utils.table_handler import flatten_table_rows


class UPSCTextReconstructor:

    # ------------------------------------------------------
    # PATTERNS
    # ------------------------------------------------------
    roman_pat = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)[\.\:]?$", re.IGNORECASE)
    statement_pat = re.compile(r"^statement[\s\-]*([i1]+)[\.\:]*$", re.IGNORECASE)
    option_pat = re.compile(r"^[\(\[]?[a-dA-D][\)\.\]]?")
    list_digit_pat = re.compile(r"^\d+\.$")
    list_digit_item_pat = re.compile(r"^\d+\s*[\.\)]\s+")
    table_sep_pat = re.compile(r"[|]{1,}")  # detect tables

    # ------------------------------------------------------
    # CLEAN + PREPROCESS RAW LINES
    # ------------------------------------------------------
    def preprocess(self, text: str):
        text = text.replace("\u00A0", " ").replace("\u200B", "")
        text = re.sub(r"[•●■▪▫]", "", text)

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        return lines

    # ------------------------------------------------------
    # CHECK PATTERNS
    # ------------------------------------------------------
    def is_option(self, line): 
        return bool(self.option_pat.match(line))

    def is_roman(self, line):
        return bool(self.roman_pat.match(line))

    def is_statement_header(self, line):
        return bool(self.statement_pat.match(line))

    def is_list_digit_header(self, line):
        return bool(self.list_digit_pat.match(line))

    def is_table_row(self, line):
        return bool(self.table_sep_pat.search(line))

    # ------------------------------------------------------
    # MAIN LOGIC
    # ------------------------------------------------------
    def reconstruct(self, text: str):
        """
        Input: raw OCR text (one column)
        Output: cleaned structured text (still unsegmented)
        """

        lines = self.preprocess(text)

        structured = []
        buffer = ""
        table_rows = []

        for i, line in enumerate(lines):

            # -------------------------------
            # HANDLE TABLE ROWS
            # -------------------------------
            if self.is_table_row(line):
                table_rows.append(line)
                continue

            # if table just ended, flush it
            if table_rows:
                structured.extend(flatten_table_rows(table_rows))
                table_rows = []

            # -------------------------------
            # HANDLE OPTIONS
            # -------------------------------
            if self.is_option(line):
                if buffer:
                    structured.append(buffer.strip())
                    buffer = ""
                structured.append(line)
                continue

            # -------------------------------
            # STATEMENT HEADERS
            # -------------------------------
            if self.is_statement_header(line):
                if buffer:
                    structured.append(buffer.strip())
                    buffer = ""
                header = re.sub(r"[\.\:]+$", "", line)  # normalize ending
                structured.append(f"{header}:")
                continue

            # -------------------------------
            # ROMAN HEADERS
            # -------------------------------
            if self.is_roman(line):
                # Example:
                # I.
                # Bonds
                numeral = line.rstrip(".:") + "."
                # If next line exists and is not roman → merge
                if i + 1 < len(lines) and not self.is_roman(lines[i + 1]):
                    merged = f"{numeral} {lines[i+1]}"
                    structured.append(merged)
                    continue
                else:
                    structured.append(numeral)
                    continue

            # -------------------------------
            # DIGIT-LIST ITEMS
            # e.g. "1. Pyroclastic debris"
            # -------------------------------
            if self.is_list_digit_header(line):
                # A lonely "1." line → merge with next
                if i + 1 < len(lines):
                    merged = f"{line} {lines[i+1]}"
                    structured.append(merged)
                    continue
                else:
                    structured.append(line)
                    continue

            if self.list_digit_item_pat.match(line):
                # Already full item, keep as-is
                structured.append(line)
                continue

            # -------------------------------
            # NORMAL TEXT LINES (MERGE LOGIC)
            # -------------------------------
            # NEW rule:
            # merge lines unless previous line ended cleanly
            if not buffer:
                buffer = line
            else:
                # If previous ended with terminal punctuation, commit & start new
                if buffer.endswith((".", "?", "!", ":")):
                    structured.append(buffer)
                    buffer = line
                else:
                    buffer += " " + line

        # flush buffer
        if buffer:
            structured.append(buffer.strip())

        # flush table if at end
        if table_rows:
            structured.extend(flatten_table_rows(table_rows))

        # final cleanup
        structured = [re.sub(r" {2,}", " ", s) for s in structured]

        # join with newline (block detector will segment later)
        return "\n".join(structured).strip()


# convenience function (so post_cleaner.py stays backward compatible)
def reconstruct_text(text: str):
    return UPSCTextReconstructor().reconstruct(text)
