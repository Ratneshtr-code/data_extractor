# phase2/option_normalizer.py
# ------------------------------------------------------
# Option Normalizer for A/B/C/D/E
# ------------------------------------------------------
# Cleans OCR variants:
#   (a), a), A), a., A., (A., etc.
# Ensures final output always uses:
#   A, B, C, D, E
# ------------------------------------------------------

import re


class OptionNormalizer:

    # Patterns like (a), a), A), (A), A.
    option_label_pat = re.compile(r"^[\(\[]?\s*([a-eA-E])[\)\.\]]?\s*", re.IGNORECASE)

    def normalize(self, options_dict):
        """
        Input:  {"a": "...", "c)": "...", "(d)": "..."}
        Output: {"A": "...", "B": "...", "C": "...", ...}
        """

        if not isinstance(options_dict, dict):
            return {}

        cleaned = {}

        for raw_key, value in options_dict.items():

            # Extract option label
            m = self.option_label_pat.match(str(raw_key).strip())
            if not m:
                continue

            label = m.group(1).upper()  # normalize to uppercase

            # Clean label text also inside the content
            # Example: "(a) only" → "only"
            cleaned_value = self._clean_option_value(value)

            cleaned[label] = cleaned_value.strip()

        # Sort by letter
        final = {}
        for letter in ["A", "B", "C", "D", "E"]:
            if letter in cleaned:
                final[letter] = cleaned[letter]

        return final


    def _clean_option_value(self, value: str):
        """
        Remove OCR prefix like: "(a)" from the actual option text.
        """
        if not isinstance(value, str):
            return ""

        v = value.strip()
        v = re.sub(r"^[\(\[]?\s*[a-eA-E][\)\.\]]?\s*", "", v)
        return v


# convenience function
def normalize_options(options_dict):
    return OptionNormalizer().normalize(options_dict)
