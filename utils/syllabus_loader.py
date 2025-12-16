import json
import os

def load_syllabus(exam: str) -> str:
    """
    Loads syllabus JSON and formats it as prompt-ready text.
    """
    path = f"syllabus/{exam}.json"

    if not os.path.exists(path):
        raise FileNotFoundError(f"Syllabus not found for exam: {exam}")

    with open(path, "r", encoding="utf-8") as f:
        syllabus = json.load(f)

    lines = []
    for subject, topics in syllabus.items():
        lines.append(f"{subject}:")
        for t in topics:
            lines.append(f"- {t}")
        lines.append("")

    return "\n".join(lines).strip()
