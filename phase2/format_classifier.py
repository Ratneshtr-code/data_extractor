# phase2/format_classifier.py
# ---------------------------------------------------------
# UPSC-Aware Question Format Classifier (Final Version)
# ---------------------------------------------------------
# Detects:
#   • single
#   • statement
#   • table
#   • match
#   • assertion
#   • paragraph
#
# Rules:
#   - 2+ numeric list items → statement
#   - 2+ roman list items → statement
#   - "Statement I" + "Statement II" → statement
#   - any '|' → table
#   - long multi-sentence text → paragraph
# ---------------------------------------------------------

import re


class FormatClassifier:

    def classify(self, text: str):
        if not text:
            return "single"

        qt = text.lower().strip()

        # ----------------------------------------------------
        # 1. TABLE DETECTION — detect BEFORE anything else
        # ----------------------------------------------------
        # Direct table pipes
        if "|" in text:
            return "table"

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        # Heuristic: If ≥2 lines contain 2+ whitespace-separated chunks → table
        # Example OCR table flattening: "Directorate   Enforcement   MHA"
        multi_col_lines = 0
        for ln in lines:
            chunks = [c for c in ln.split(" ") if c.strip()]
            if len(chunks) >= 3:
                multi_col_lines += 1
        if multi_col_lines >= 2:
            return "table"

        # Header cues for tables
        if any(h in qt for h in ["organization", "functions", "works under", "column i", "column ii"]):
            # If the block contains multiple short lines, very likely table
            short_lines = sum(1 for ln in lines if len(ln) < 35)
            if short_lines >= 3:
                return "table"

        # ----------------------------------------------------
        # 2. STATEMENT DETECTION (Fix for your Bug #1)
        # ----------------------------------------------------

        # Count numeric list items (1., 2., 3.)
        numeric_items = re.findall(r"\b\d+\.", text)
        if len(numeric_items) >= 2:
            return "statement"

        # Count Roman numerals
        roman_items = re.findall(r"\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\.", text)
        if len(roman_items) >= 2:
            return "statement"

        # Detect OCR-broken statement headers
        if "statement i" in qt or "statement ii" in qt:
            return "statement"

        if "consider the following statements" in qt:
            return "statement"

        # Bullet-like patterns: (1), 1), (a), (b)
        if len(re.findall(r"^\(?\d+\)|^\(?[a-d]\)", text, flags=re.MULTILINE)) >= 2:
            return "statement"

        # ----------------------------------------------------
        # 3. MATCH THE FOLLOWING
        # ----------------------------------------------------
        if "match the following" in qt:
            return "match"

        # ----------------------------------------------------
        # 4. ASSERTION–REASON
        # ----------------------------------------------------
        if "assertion" in qt and "reason" in qt:
            return "assertion"

        # ----------------------------------------------------
        # 5. PARAGRAPH QUESTIONS
        # ----------------------------------------------------
        if any(k in qt for k in ["read the following", "paragraph", "passage"]):
            return "paragraph"

        if text.count(".") >= 5:  # long paragraph style
            return "paragraph"

        # ----------------------------------------------------
        # DEFAULT
        # ----------------------------------------------------
        return "single"

