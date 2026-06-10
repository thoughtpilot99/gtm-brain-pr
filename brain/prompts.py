"""Load the runtime prompts from the editable files in prompts/.

Keeping the judge and drafting prompts in plain files (not buried in code) means
you tune the brain's reasoning and voice without touching Python, and what you
read in prompts/judge.md is exactly what the model sees. Lines starting with #
are treated as notes and stripped.
"""

import os

_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")


def load_prompt(filename: str, fallback: str = "") -> str:
    path = os.path.join(_PROMPTS_DIR, filename)
    try:
        with open(path) as f:
            body = [ln for ln in f.read().splitlines() if not ln.lstrip().startswith("#")]
        text = "\n".join(body).strip()
        return text or fallback
    except FileNotFoundError:
        return fallback
