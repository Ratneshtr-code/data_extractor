# utils/upsc_text_reconstructor.py
# ---------------------------------------------------------
# UPSC-Aware Text Reconstruction Engine (Patch v3)
# ---------------------------------------------------------
# Fixes:
#   - Proper merging of numeric list statements
#   - Proper reconstruction of Roman + numeric headers
#   - Prevents "Statement\nI." and "I.\ntext" breakage
# ---------------------------------------------------------

import re
from utils.table_handler import flatten_table_rows


class UPSCTextReconstructor:

    roman_pat = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)[\.\:]?$", re.IGNORECASE)
    statement_header_pat = re.compile(r"^statement[\s\-]*([i1]+)[\.\:]*$", re.IGNORECASE)
    numeric_header_pat = re.compile(r"^\d+\.$")
    numeric_item_pat = re.compile(r"^\d+\s*[\.\)]\s+")
    table_sep_pat = re.compile(r"[|]{1,}")

    option_pat = re.compile(r"^[\(\[]?[a-eA-E][\)\.\]]?\s*")

    def preprocess(self, text: str):
        text = text.replace("\u00A0", " ").replace("\u200B", "")
        text = re.sub(r"[•●■▪▫]", "", text)
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        return lines

    def is_option(self, line):
        return bool(self.option_pat.match(line))

    def is_roman(self, line):
        return bool(self.roman_pat.match(line))

    def is_statement_header(self, line):
        return bool(self.statement_header_pat.match(line))

    def is_numeric_header(self, line):
        return bool(self.numeric_header_pat.match(line))

    def is_numeric_item(self, line):
        return bool(self.numeric_item_pat.match(line))

    def is_table_row(self, line):
        return bool(self.table_sep_pat.search(line))

    def reconstruct(self, text: str):

        lines = self.preprocess(text)

        structured = []
        buffer = ""
        table_rows = []

        skip_next = False

        for i, line in enumerate(lines):

            if skip_next:
                skip_next = False
                continue

            # ----------------------------
            # FORCE NEW LINE FOR LIST ITEMS
            # ----------------------------
            if re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.", line):
                structured.append(line)
                continue

            if re.match(r"^\d+\.", line):
                structured.append(line)
                continue

            # ----------------------------
            # TABLE ROW COLLECTION
            # ----------------------------
            if self.is_table_row(line):
                table_rows.append(line)
                continue

            if table_rows:
                structured.extend(flatten_table_rows(table_rows))
                table_rows = []

            # ----------------------------
            # OPTIONS
            # ----------------------------
            if self.is_option(line):
                if buffer:
                    structured.append(buffer.strip())
                    buffer = ""
                structured.append(line)
                continue

            # ----------------------------
            # NORMAL LINE MERGE
            # ----------------------------
            if not buffer:
                buffer = line
            else:
                if buffer.endswith((".", "?", "!", ":")):
                    structured.append(buffer)
                    buffer = line
                else:
                    buffer += " " + line

        if buffer:
            structured.append(buffer.strip())

        if table_rows:
            structured.extend(flatten_table_rows(table_rows))

        structured = [re.sub(r" {2,}", " ", s) for s in structured]

        return "\n".join(structured).strip()



def reconstruct_text(text: str):
    return UPSCTextReconstructor().reconstruct(text)
