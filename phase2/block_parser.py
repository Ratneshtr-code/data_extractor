# phase2/block_parser.py
# ------------------------------------------------------
# UPSC / PSC / EXAM-AWARE BLOCK PARSER
# ------------------------------------------------------
# - Parses ONE question block using Groq LLM
# - Dynamically injects exam syllabus into system prompt
# - Enforces syllabus-bounded subject/topic tagging
# ------------------------------------------------------

import os
from groq import Groq
from dotenv import load_dotenv

from utils.syllabus_loader import load_syllabus

# ------------------------------------------------------
# ENV + CLIENT
# ------------------------------------------------------
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("Missing GROQ_API_KEY")

client = Groq(api_key=API_KEY)

MODEL = "llama-3.3-70b-versatile"

# ------------------------------------------------------
# LOAD SYSTEM PROMPT TEMPLATE
# ------------------------------------------------------
PROMPT_PATH = "phase2/prompts/parse_block_system.txt"

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    PARSE_BLOCK_SYSTEM_PROMPT = f.read()

# ------------------------------------------------------
# HELPERS
# ------------------------------------------------------

def _extract_exam_from_tag(tag: str) -> str:
    """
    tag example:
      UPSC_2025_p1_c1_block3

    returns:
      UPSC
    """
    parts = tag.split("_")

    exam_parts = []
    for p in parts:
        if p.isdigit():   # year detected
            break
        exam_parts.append(p)

    if not exam_parts:
        raise ValueError(f"Cannot extract exam from tag: {tag}")

    return "_".join(exam_parts)



# ------------------------------------------------------
# MAIN ENTRY
# ------------------------------------------------------

def parse_block(block_text: str, tag: str) -> str:
    """
    Sends ONE question block to Groq LLM with
    dynamically injected syllabus.

    Returns:
        Raw LLM response (string)
    """

    # -------------------------------
    # DETERMINE EXAM
    # -------------------------------
    exam = _extract_exam_from_tag(tag)

    # -------------------------------
    # LOAD SYLLABUS
    # -------------------------------
    try:
        syllabus_text = load_syllabus(exam)
    except FileNotFoundError as e:
        raise RuntimeError(
            f"[SYLLABUS ERROR] {e}\n"
            f"Expected file: syllabus/{exam}.json"
        )

    # -------------------------------
    # INJECT SYLLABUS INTO PROMPT
    # -------------------------------
    system_prompt = PARSE_BLOCK_SYSTEM_PROMPT.replace(
        "{{SYLLABUS}}",
        syllabus_text
    )

    # -------------------------------
    # CALL GROQ LLM
    # -------------------------------
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": block_text}
        ],
        temperature=0,
        max_tokens=2048
    )

    return response.choices[0].message.content
