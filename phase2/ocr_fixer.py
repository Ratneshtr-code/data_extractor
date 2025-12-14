# phase2/ocr_fixer.py
# --------------------------------------------------------------
# Safe, conservative fixes for extremely common OCR glitches.
# We only fix cases that are 100% unambiguous.
# --------------------------------------------------------------

import re

class SafeOCRFixer:

    def fix_option(self, option_text: str):
        t = option_text

        # Missing "A" in "All"
        if t.startswith("ll "):
            return "All " + t[3:]

        if t.startswith("ll the "):
            return "All the " + t[7:]

        # Missing "B" in "Both"
        if t.startswith("oth "):
            return "Both " + t[4:]

        return t
