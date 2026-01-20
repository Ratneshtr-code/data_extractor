# phase2/table_formatter.py
# --------------------------------------------------------------
# Table question formatter - Formats table questions with proper structure
# Handles both tables with pipes (|) and tables without pipes (OCR lost them)
# --------------------------------------------------------------

import re

class TableFormatter:

    def format(self, text: str):
        """
        Format table question text with proper line breaks and structure.
        Only handles tables that already have pipes - normalize spacing.
        """
        if not text:
            return text
        
        # If text has pipes, normalize spacing
        if "|" in text:
            lines = text.split("\n")
            out = []
            for ln in lines:
                if "|" in ln:
                    cols = [c.strip() for c in ln.split("|")]
                    out.append(" | ".join(cols))
                else:
                    out.append(ln)
            return "\n".join(out)
        
        # No pipes - return as-is (don't try to reconstruct)
        return text
