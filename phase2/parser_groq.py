import os
from dotenv import load_dotenv
from groq import Groq

# Load API key
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY missing in .env")

client = Groq(api_key=API_KEY)

# Paths
PROMPT_FILE = "phase2/prompts/extract_question.txt"
LOG_DIR = "logs/groq_raw"
os.makedirs(LOG_DIR, exist_ok=True)

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()


def call_groq(prompt_text, block_id="unknown"):
    """
    Sends prompt to Groq and logs raw output.
    """
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You must output STRICT VALID JSON only.\n"
                    "Escape every newline inside strings as \\n.\n"
                    "Never include unescaped raw line breaks inside JSON strings.\n"
                    "Never include commentary.\n"
                ),
            },
            {"role": "user", "content": prompt_text},
        ],
        max_tokens=2048,
        temperature=0,
    )

    content = resp.choices[0].message.content

    # Log raw output
    with open(f"{LOG_DIR}/response_{block_id}.txt", "w", encoding="utf-8") as f:
        f.write(content)

    return content


def request_json_repair(bad_json, block_id="unknown"):
    """
    Ask Groq to FIX broken JSON and return valid JSON.
    """
    repair_prompt = f"""
The following JSON is invalid. Fix it and return valid STRICT JSON only.
Do NOT change any text content inside the question or options.
Escape all newlines as \\n.

Broken JSON:
----------------
{bad_json}
----------------
"""

    return call_groq(repair_prompt, f"{block_id}_repair")


def parse_question_block(block_text, block_id="block"):
    """
    Sends the OCR block to Groq for strict, non-rephrasing structure extraction.
    """
    final_prompt = BASE_PROMPT + f"""

OCR Text to Parse:
--------------------
{block_text}
--------------------
"""

    raw_json = call_groq(final_prompt, block_id)
    return raw_json
