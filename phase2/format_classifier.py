# phase2/format_classifier.py
# ---------------------------------------------------------
# UPSC-Aware Question Format Classifier (FINAL, LOCKED)
# ---------------------------------------------------------

import re

class FormatClassifier:

    def classify(self, text: str):

        if not text:
            return "single"

        qt = text.lower()

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        # ----------------------------------------------------
        # 1. MATCH / PAIRS (HIGHEST PRIORITY)
        # ----------------------------------------------------

        # Rule 0: "correctly matched"
        if re.search(r"correctly matched", qt):
            return "match"

        # Rule 1: Roman numeral colon pairs
        roman_pairs = re.findall(
            r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+.+\s+:\s+.+",
            text,
            flags=re.MULTILINE
        )
        if len(roman_pairs) >= 2:
            return "match"

        # Rule 2: Numbered dash pairs
        dash_pairs = re.findall(
            r"^\d+\.\s+.+\s+[-–—]\s+.+",
            text,
            flags=re.MULTILINE
        )
        if len(dash_pairs) >= 2:
            return "match"

        # Rule 3: Sequence matching
        if "sequence is correct" in qt:
            return "match"

        # ----------------------------------------------------
        # 2. TABLE (DATA TABLE, NOT PAIRS)
        # ----------------------------------------------------
        if "|" in text:
            return "table"

        multi_col_lines = 0
        for ln in lines:
            if len(ln.split()) >= 3:
                multi_col_lines += 1
        if multi_col_lines >= 3 and "matched" not in qt:
            return "table"

        # ----------------------------------------------------
        # 3. STATEMENT QUESTIONS
        # ----------------------------------------------------
        if "consider the following statements" in qt:
            return "statement"

        if len(re.findall(r"\b\d+\.", text)) >= 2:
            return "statement"

        if len(re.findall(r"\b(I|II|III|IV|V)\.", text)) >= 2:
            return "statement"

        # ----------------------------------------------------
        # 4. ASSERTION – REASON
        # ----------------------------------------------------
        if "assertion" in qt and "reason" in qt:
            return "assertion"

        # ----------------------------------------------------
        # 5. PARAGRAPH
        # ----------------------------------------------------
        if any(k in qt for k in ["read the following", "paragraph", "passage"]):
            return "paragraph"

        if text.count(".") >= 5:
            return "paragraph"

        # ----------------------------------------------------
        # DEFAULT
        # ----------------------------------------------------
        return "single"
