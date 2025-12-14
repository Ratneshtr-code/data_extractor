# phase2/segmenter_groq.py
# -------------------------------------------------------------
# LLM-Based UPSC Column Segmenter
# -------------------------------------------------------------
# Input:  Full cleaned OCR column text
# Output: JSON array of individual question blocks
#
# This replaces regex segmentation completely.
# -------------------------------------------------------------

import os
import json
from groq import Groq

SEGMENT_PROMPT_PATH = "phase2/prompts/segment_column.txt"

# Load system prompt
with open(SEGMENT_PROMPT_PATH, "r", encoding="utf-8") as f:
    SEGMENT_SYSTEM_PROMPT = f.read()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("Missing GROQ_API_KEY")

client = Groq(api_key=API_KEY)


class ColumnSegmenter:

    def __init__(self, model="llama-3.3-70b-versatile"):
        self.model = model

    def segment(self, text: str, tag: str):
        """
        Sends one full column OCR text to LLM for question block segmentation.
        """
        user_prompt = (
            "OCR COLUMN TEXT:\n"
            "-----------------\n"
            f"{text.strip()}"
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SEGMENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=4096,
        )

        content = response.choices[0].message.content

        # Log for debugging
        self._log_raw(tag, content)

        return self._extract_json(content)


    def _log_raw(self, tag, content):
        os.makedirs("logs/groq_segment_raw", exist_ok=True)

        # sanitize tag
        safe = tag.replace("/", "_").replace("\\", "_")

        path = f"logs/groq_segment_raw/{safe}.txt"

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


    def _extract_json(self, s):
        """
        Extract the JSON array from model output.
        """
        start = s.find("[")
        end = s.rfind("]")
        if start == -1 or end == -1:
            return []

        try:
            arr = json.loads(s[start:end + 1])
            if isinstance(arr, list):
                return arr
            return []
        except:
            return []


def segment_column(text: str, tag: str):
    return ColumnSegmenter().segment(text, tag)
