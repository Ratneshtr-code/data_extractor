# utils/upsc_question_block_detector.py
# ------------------------------------------------------
# UPSC-Aware Question Block Detector (Quick Fix v2)
# ------------------------------------------------------
# This version correctly handles:
#   - multi-line UPSC stems
#   - roman numeral continuation
#   - list continuation (1., 2., 3.)
#   - table blocks
#   - avoids accidental merges
#   - avoids accidental splits
# ------------------------------------------------------

import re


class UPSCQuestionBlockDetector:

    # --------------------------------------------------
    # PATTERNS
    # --------------------------------------------------

    option_pat = re.compile(r"^[\(\[]?\s*([a-dA-D])[\)\.\]]?\s")
    roman_pat = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)[\.\:]", re.IGNORECASE)
    digit_list_pat = re.compile(r"^\d+\s*[\.\)]\s+")
    table_pat = re.compile(r"[A-Za-z0-9]+\s*\|\s*[A-Za-z0-9]+")

    likely_q_start = [
        r"^with reference",
        r"^consider the following",
        r"^which of the following",
        r"^which one of the following",
        r"^assertion",
        r"^read the following",
        r"^regarding",
        r"^in the context",
        r"^who among the following",
        r"^identify the correct",
        r"^identify which",
    ]

    compiled_starts = [re.compile(p, re.IGNORECASE) for p in likely_q_start]

    # --------------------------------------------------
    # OPTION CHECK
    # --------------------------------------------------
    def is_option(self, line: str):
        return bool(self.option_pat.match(line.strip()))

    # --------------------------------------------------
    # PROBABLE QUESTION START
    # --------------------------------------------------
    def is_probable_question_start(self, line: str):
        low = line.lower().strip()

        # ignore extremely short lines
        if len(low) < 15:
            return False

        # WH-question starts
        if re.match(r"^(which|what|when|where|who|identify)\b", low) and len(low.split()) > 3:
            return True

        # specific UPSC known stems
        for pat in self.compiled_starts:
            if pat.match(line):
                return True

        # “How many…” long question stems
        if low.startswith("how many") and len(low.split()) > 3:
            return True

        # final sentences ending with '?'
        if low.endswith("?") and len(low.split()) > 4:
            return True

        return False

    # --------------------------------------------------
    # MAIN DETECTOR
    # --------------------------------------------------
    def detect(self, text: str):
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        blocks = []
        curr = []

        for idx, line in enumerate(lines):

            # --------------------------
            # TABLE CONTINUATION
            # --------------------------
            if self.table_pat.search(line):
                curr.append(line)
                continue

            # --------------------------
            # LIST CONTINUATION 1., 2., 3.
            # --------------------------
            if self.digit_list_pat.match(line):
                curr.append(line)
                continue

            # --------------------------
            # ROMAN NUMERAL continuation
            # --------------------------
            if self.roman_pat.match(line):
                curr.append(line)
                continue

            # --------------------------
            # OPTION continuation
            # --------------------------
            if self.is_option(line):
                curr.append(line)
                continue

            # --------------------------
            # LOWCASE continuation
            # e.g. “Alternative Investment Funds?”
            # --------------------------
            if curr and line[0].islower():
                curr.append(line)
                continue

            # --------------------------
            # SHORT FRAGMENT continuation
            # (avoid splitting small follow-up lines)
            # --------------------------
            if curr and len(line.split()) <= 3:
                curr.append(line)
                continue

            # --------------------------
            # NEW QUESTION START
            # --------------------------
            if self.is_probable_question_start(line):

                # If previous question is too small, merge
                if curr and len(" ".join(curr).split()) < 5:
                    curr.append(line)
                    continue

                # Commit previous block
                if curr:
                    blocks.append("\n".join(curr).strip())
                    curr = []

                curr.append(line)
                continue

            # --------------------------
            # DEFAULT: continuation
            # --------------------------
            curr.append(line)

        # flush last block
        if curr:
            blocks.append("\n".join(curr).strip())

        return blocks


# convenience function
def detect_question_blocks(text: str):
    return UPSCQuestionBlockDetector().detect(text)
