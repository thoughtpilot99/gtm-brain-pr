"""Organ 3 - JUDGE.

The reasoning layer, and the actual moat. Sending is commodity. Deciding which
account is hot, why now, and what the play should be is not.

The judge reads the new signal AND the account's full memory AND your ICP, then
returns a structured verdict. Memory is what makes this more than a classifier:
a third funding round means something different if you already emailed them twice
and got silence.
"""

import json
import os
from typing import List

from .models import Signal, Verdict
from .memory import Memory
from .prompts import load_prompt

DEFAULT_MODEL = os.environ.get("GTM_BRAIN_MODEL", "claude-sonnet-4-6")

# Loaded from prompts/judge.md so you can tune the brain's reasoning without
# touching code. The string below is the fallback if that file is missing.
_FALLBACK = (
    "You are the judgment layer of a GTM brain. You decide, for one account, "
    "whether a buying signal is worth acting on right now. You are given the ICP, "
    "the new signals this run, and the full history of prior signals, messages, "
    "and outcomes. Return only JSON: score (0-100), why_now (one sentence a "
    "salesperson could quote back to the buyer), play (first_touch, follow_up, "
    "nurture, skip), rationale. Rules: if we touched them in the last 7 days, "
    "prefer nurture or skip. If the signal is weak or off-ICP, score low and skip. "
    "Saying no is the job too. why_now must reference the real trigger, never a "
    "generic value prop."
)
SYSTEM = load_prompt("judge.md", _FALLBACK)


def _ask_claude(prompt: str, model: str) -> dict:
    from anthropic import Anthropic

    client = Anthropic()  # reads ANTHROPIC_API_KEY
    resp = client.messages.create(
        model=model,
        max_tokens=512,
        temperature=0,  # deterministic scoring
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    # The model is told to return bare JSON; be forgiving if it fences it.
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
    return json.loads(text)


def judge(account: str, new_signals: List[Signal], icp: dict,
          memory: Memory, model: str = DEFAULT_MODEL,
          offline: bool = False) -> Verdict:
    history = memory.history(account)
    last_touch = memory.last_touch_age_days(account)

    if offline:
        return _heuristic(account, new_signals, last_touch)

    prompt = json.dumps({
        "icp": icp,
        "new_signals": [{"bucket": s.bucket, "summary": s.summary} for s in new_signals],
        "history": history,
        "days_since_last_touch": last_touch,
    }, indent=2)

    try:
        data = _ask_claude(prompt, model)
        return Verdict(
            account=account,
            score=int(data.get("score", 0)),
            why_now=str(data.get("why_now", "")),
            play=str(data.get("play", "skip")),
            rationale=str(data.get("rationale", "")),
        )
    except Exception as e:  # network down, bad key, malformed JSON
        v = _heuristic(account, new_signals, last_touch)
        v.rationale = f"(fell back to heuristic: {e})"
        return v


def _heuristic(account: str, new_signals: List[Signal], last_touch) -> Verdict:
    """No-LLM fallback so the loop always runs. Crude on purpose."""
    weight = {"funding": 35, "job": 25, "company": 20, "social": 15}
    score = min(100, sum(weight.get(s.bucket, 10) for s in new_signals))
    if last_touch is not None and last_touch < 7:
        play = "nurture" if score >= 50 else "skip"
    else:
        play = "first_touch" if score >= 40 else "skip"
    top = max(new_signals, key=lambda s: weight.get(s.bucket, 0))
    return Verdict(account=account, score=score,
                   why_now=top.summary, play=play,
                   rationale="heuristic scoring (offline)")
