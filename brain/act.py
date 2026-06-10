"""Organ 4 - ACT.

Draft a message grounded in the trigger, then hand it to a delivery adapter.

The one rule: the message quotes why you reached out now. If it could have been
sent yesterday or next month with no change, the brain didn't do its job. No
"Hi {{firstName}}". The signal is the opener.
"""

import json
import os
from typing import Optional

from .models import Verdict, Signal, Draft
from .memory import Memory
from .prompts import load_prompt

DEFAULT_MODEL = os.environ.get("GTM_BRAIN_MODEL", "claude-sonnet-4-6")

# Loaded from prompts/draft.md so you can tune the brain's voice without touching
# code. The string below is the fallback if that file is missing.
_FALLBACK = (
    "You write the first lines of outbound for a GTM brain. You are given a "
    "buying signal, the play, and the sender's guardrails. Write a subject and "
    "three to five sentences that open on the actual trigger, connect it to one "
    "problem the sender solves in one line, and end with a low-friction ask. No "
    "fake urgency, no \"circling back\", no em dashes, and never \"Hi "
    "{{firstName}}\". Return only JSON with subject and body."
)
SYSTEM = load_prompt("draft.md", _FALLBACK)


def _ask_claude(prompt: str, model: str) -> dict:
    from anthropic import Anthropic

    client = Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        temperature=0.3,  # a little room for natural phrasing
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
    return json.loads(text)


def act(verdict: Verdict, trigger: Signal, sequences: dict, delivery,
        memory: Memory, model: str = DEFAULT_MODEL,
        dry_run: bool = True, offline: bool = False,
        prompt_variant: str = "v1") -> Optional[int]:
    """Draft for this play, send (or print), and remember the touch."""
    if verdict.play == "skip":
        return None

    intent = sequences.get(verdict.play, {})
    draft = _draft(verdict, trigger, intent, model, offline, prompt_variant)

    send_id = delivery.send(draft, dry_run=dry_run)
    touch_id = memory.record_touch(draft, send_id)
    return touch_id


def _draft(verdict: Verdict, trigger: Signal, intent: dict,
           model: str, offline: bool, prompt_variant: str) -> Draft:
    if offline:
        return _template(verdict, trigger, prompt_variant)

    prompt = json.dumps({
        "trigger": trigger.summary,
        "bucket": trigger.bucket,
        "why_now": verdict.why_now,
        "play": verdict.play,
        "guardrails": intent,
    }, indent=2)
    try:
        data = _ask_claude(prompt, model)
        return Draft(account=verdict.account, contact=trigger.contact,
                     subject=data.get("subject", ""), body=data.get("body", ""),
                     play=verdict.play, prompt_variant=prompt_variant)
    except Exception:
        return _template(verdict, trigger, prompt_variant)


def _template(verdict: Verdict, trigger: Signal, prompt_variant: str) -> Draft:
    """No-LLM fallback. Still trigger-grounded, just not as good."""
    subject = f"about your {trigger.bucket} move"
    body = (f"Saw that you {trigger.summary}. That usually means a specific problem is "
            f"now on someone's desk. Worth a 15-minute look at how we handle it? "
            f"Happy to send a one-pager instead if that's easier.")
    return Draft(account=verdict.account, contact=trigger.contact,
                 subject=subject, body=body, play=verdict.play,
                 prompt_variant=prompt_variant)
