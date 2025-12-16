# utils/upsc_question_block_detector.py
# --------------------------------------------------------
# UPSC-Aware Block Detector (Patch v3)
# --------------------------------------------------------

import re


class UPSCQuestionBlockDetector:

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

    def is_option(self, line: str):
        return bool(self.option_pat.match(line.strip()))

    def is_probable_question_start(self, line: str):
        low = line.lower().strip()

        # NEVER treat numeric list as question start
        if re.match(r"^\d+\.", low):
            return False

        if len(low) < 10:
            return False

        if re.match(r"^(which|what|when|where|who|identify)\b", low) and len(low.split()) > 3:
            return True

        for pat in self.compiled_starts:
            if pat.match(line):
                return True

        if low.startswith("how many") and len(low.split()) > 3:
            return True

        if low.endswith("?") and len(low.split()) > 4:
            return True

        return False

    def detect(self, text: str):

        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        blocks = []
        curr = []

        for idx, line in enumerate(lines):

            if self.table_pat.search(line):
                curr.append(line)
                continue

            if self.digit_list_pat.match(line):
                curr.append(line)
                continue

            if self.roman_pat.match(line):
                curr.append(line)
                continue

            if self.is_option(line):
                curr.append(line)
                continue

            if curr and line[0].islower():
                curr.append(line)
                continue

            if curr and len(line.split()) <= 3:
                curr.append(line)
                continue

            if self.is_probable_question_start(line):

                if curr and len(" ".join(curr).split()) < 5:
                    curr.append(line)
                    continue

                if curr:
                    blocks.append("\n".join(curr).strip())
                    curr = []

                curr.append(line)
                continue

            curr.append(line)

        if curr:
            blocks.append("\n".join(curr).strip())

        return blocks


def detect_question_blocks(text: str):
    return UPSCQuestionBlockDetector().detect(text)
