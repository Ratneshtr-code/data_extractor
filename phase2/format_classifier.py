# phase2/format_classifier.py
# --------------------------------------------------------------
# Determine question format: single, statement, table, match,
# assertion, paragraph
# --------------------------------------------------------------

import re

class FormatClassifier:

    def classify(self, question_text: str):
        qt = question_text.lower()

        # ---------------------------
        # TABLE
        # ---------------------------
        if "|" in question_text:
            return "table"
        if re.search(r"\b(works under|functions|organization)\b", qt) and \
           re.search(r"\b(i\.)\s", qt):
            return "table"

        # ---------------------------
        # STATEMENT
        # ---------------------------
        if "consider the following statements" in qt:
            return "statement"
        if re.search(r"statement\s+i\.", qt):
            return "statement"
        if re.search(r"\bi\.\s", qt) and re.search(r"\bii\.\s", qt):
            return "statement"

        # ---------------------------
        # MATCH THE FOLLOWING
        # ---------------------------
        if "match the following" in qt:
            return "match"
        if re.search(r"^[a-d]\.", qt) and re.search(r"\b1\.", qt):
            return "match"

        # ---------------------------
        # ASSERTION–REASON
        # ---------------------------
        if "assertion (a)" in qt and "reason (r)" in qt:
            return "assertion"
        if "assertion:" in qt and "reason:" in qt:
            return "assertion"

        # ---------------------------
        # PARAGRAPH
        # ---------------------------
        if "read the following" in qt:
            return "paragraph"
        if len(qt.split(".")) > 5:  # long descriptive passage
            return "paragraph"

        # Default
        return "single"
