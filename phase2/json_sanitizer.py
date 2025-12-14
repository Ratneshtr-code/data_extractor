# phase2/json_sanitizer.py
# ------------------------------------------------------
# FIXED JSON SANITIZER
# ------------------------------------------------------
# The old version corrupted JSON by replacing newlines.
# This version:
#   - Removes control characters safely
#   - Extracts the JSON object/array from the LLM output
#   - Returns parsed dict or list
#   - Never rewrites line breaks
# ------------------------------------------------------

import json
import re


def sanitize_and_load(s: str):
    if not isinstance(s, str):
        return None

    # Remove control characters (safe)
    s = re.sub(r"[\x00-\x09\x0B-\x1F\x7F]", "", s)

    # Detect JSON start (object or array)
    start_obj = s.find("{")
    start_arr = s.find("[")
    start = min(x for x in [start_obj, start_arr] if x != -1)

    # Detect JSON end (object or array)
    end_obj = s.rfind("}")
    end_arr = s.rfind("]")
    end = max(end_obj, end_arr)

    if start == -1 or end == -1 or end <= start:
        return None

    json_str = s[start : end + 1].strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None
