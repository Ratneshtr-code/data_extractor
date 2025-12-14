# phase2/block_parser.py
# ------------------------------------------------------
# Per-Block LLM Parser
# ------------------------------------------------------
# Input  : One UPSC question block (string)
# Output : JSON representing one cleaned, structured question
#
# This replaces the old "parse_full_column" mechanism.
# ------------------------------------------------------

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Load system prompt
SYSTEM_PROMPT_FILE = "phase2/prompts/parse_block_system.txt"

with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Load environment API key
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("Missing GROQ_API_KEY")

client = Groq(api_key=API_KEY)


class BlockParser:

    def __init__(self):
        self.model_name = "llama-3.3-70b-versatile"

    def parse_block(self, block_text: str, tag: str):
        """
        Parse a single question block into JSON using the Groq LLM.
        """

        user_prompt = (
            "QUESTION BLOCK:\n"
            "----------------\n"
            f"{block_text.strip()}"
        )

        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2048,
            temperature=0,
        )

        content = response.choices[0].message.content

        # optional logging
        self.log_raw_response(tag, content)

        return content


    def log_raw_response(self, tag, content):
        os.makedirs("logs/groq_raw_blocks", exist_ok=True)
        safe_tag = tag.replace("/", "_").replace("\\", "_")
        path = f"logs/groq_raw_blocks/{safe_tag}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


# convenience function
def parse_block(block_text: str, tag: str):
    return BlockParser().parse_block(block_text, tag)
