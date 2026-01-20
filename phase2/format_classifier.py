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
        # 1. TABLE (HIGHEST PRIORITY - Check for structured tables)
        # ----------------------------------------------------
        # SIMPLE RULE: If "|" is present anywhere in text, classify as "table" format
        # This is the definitive indicator of table structure
        if "|" in text:
            return "table"

        # ----------------------------------------------------
        # 2. MATCH / PAIRS (Check after table to avoid misclassification)
        # ----------------------------------------------------
        # Rule 0: "correctly matched" - but only if NOT already classified as table
        if re.search(r"correctly matched", qt):
            return "match"

        # Rule 1: Roman numeral colon pairs (I. X : Y format)
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
