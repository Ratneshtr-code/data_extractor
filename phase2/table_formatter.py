# phase2/table_formatter.py
# --------------------------------------------------------------
# Light beautification of table questions, without paraphrasing.
# We only introduce line breaks and column separators.
# --------------------------------------------------------------

import re

class TableFormatter:

    def format(self, text: str):
        lines = text.split("\n")
        out = []

        for ln in lines:
            if "|" in ln:
                # Normalize spacing
                cols = [c.strip() for c in ln.split("|")]
                out.append(" | ".join(cols))
            else:
                out.append(ln)

        return "\n".join(out)
