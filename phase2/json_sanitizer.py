import json
import re
from phase2.parser_groq import request_json_repair


def sanitize_and_load(json_str, block_id="unknown"):
    """
    Attempts to clean + parse Groq JSON.
    If it fails, automatically requests repair from Groq.
    """
    try:
        return _try_parse(json_str)
    except Exception:
        # Request repair
        repaired = request_json_repair(json_str, block_id)

        try:
            return _try_parse(repaired)
        except Exception:
            # Last fallback: never crash
            return {
                "extracted_successfully": False,
                "error": "Could not repair JSON",
                "raw_text_excerpt": json_str[:200],
            }


def _try_parse(json_str):
    """
    Internal cleaning + parsing logic.
    """
    # Remove forbidden control characters
    json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', json_str)

    # Ensure escaped newlines inside all quoted strings
    def fix_newlines(match):
        text = match.group(1)
        text = text.replace("\n", "\\n")
        return f"\"{text}\""

    json_str = re.sub(r'"([^"]*?)"', fix_newlines, json_str, flags=re.DOTALL)

    # Trim prefix/suffix outside the JSON braces
    start = json_str.find("{")
    end = json_str.rfind("}")
    if start != -1 and end != -1:
        json_str = json_str[start : end + 1]

    return json.loads(json_str)
