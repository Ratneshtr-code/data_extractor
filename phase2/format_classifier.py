# phase2/format_classifier.py
# ------------------------------------------------------
# UPSC Question Format Classifier
# ------------------------------------------------------
# Detects one of the following types:
#   single, statement, table, match, paragraph, assertion
# ------------------------------------------------------

import re


class FormatClassifier:

    # --------------------------------------------------
    # PATTERN DEFINITIONS
    # --------------------------------------------------

    # Statement pattern
    statement_intro = re.compile(
        r"(consider the following statements|which of the following statements|statement\s*i)", 
        re.IGNORECASE
    )

    roman_pat = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)[\.\:]", re.IGNORECASE)

    # Assertion–Reason patterns
    assertion_pat = re.compile(r"assertion\s*\(", re.IGNORECASE)
    reason_pat = re.compile(r"reason\s*\(", re.IGNORECASE)

    # Table indicator
    table_pat = re.compile(r"[A-Za-z0-9]+\s*\|\s*[A-Za-z0-9]+")

    # Match-the-column indicators
    match_keywords = [
        "match the following",
        "pair", "pairs",
        "column", "list-i", "list-ii"
    ]

    # Paragraph indicators
    paragraph_intro = re.compile(
        r"(read the following|passage|paragraph)", re.IGNORECASE
    )

    # --------------------------------------------------
    # MAIN CLASSIFIER
    # --------------------------------------------------
    def classify(self, text: str):
        """
        Input: one cleaned question string
        Output: name of format
        """

        low = text.lower()

        # --------------------------------------
        # 1. ASSERTION–REASON
        # --------------------------------------
        if self.assertion_pat.search(low) or self.reason_pat.search(low):
            return "assertion"

        # --------------------------------------
        # 2. TABLE
        # --------------------------------------
        if self.table_pat.search(text):
            return "table"

        # --------------------------------------
        # 3. STATEMENT (Roman numerals OR "Statement I")
        # --------------------------------------
        if self.statement_intro.search(low):
            return "statement"

        if any(self.roman_pat.match(ln.strip()) for ln in text.split("\n")):
            return "statement"

        # --------------------------------------
        # 4. MATCH-THE-COLUMN
        # --------------------------------------
        for kw in self.match_keywords:
            if kw in low:
                return "match"

        # --------------------------------------
        # 5. PARAGRAPH
        # --------------------------------------
        if self.paragraph_intro.search(low):
            return "paragraph"

        # --------------------------------------
        # 6. DEFAULT → SINGLE
        # --------------------------------------
        return "single"


# convenience
def classify_format(text: str):
    return FormatClassifier().classify(text)
