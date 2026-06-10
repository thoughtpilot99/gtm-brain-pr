"""Core data types shared across the five organs.

Kept tiny on purpose. A Signal is something that moved in the world. A Verdict
is the brain's decision about it. Everything else is plumbing.
"""

from dataclasses import dataclass, field
from typing import Optional
import time

# The four buckets. Start from movement, not from a static list.
BUCKETS = ("job", "social", "company", "funding")


@dataclass
class Signal:
    account: str               # company name or domain
    bucket: str                # one of BUCKETS
    summary: str               # human-readable: "opened a Head of RevOps role"
    source: str = "stub"       # which adapter produced it
    url: str = ""              # link to the evidence, if any
    contact: str = ""          # optional person to reach at the account
    seen_at: float = field(default_factory=time.time)

    def validate(self) -> "Signal":
        if self.bucket not in BUCKETS:
            raise ValueError(
                f"unknown bucket {self.bucket!r}; expected one of {BUCKETS}"
            )
        return self


@dataclass
class Verdict:
    account: str
    score: int                 # 0-100, how hot this account is right now
    why_now: str               # one line the human (or the message) can quote
    play: str                  # first_touch | follow_up | nurture | skip
    rationale: str = ""        # the brain's reasoning, for the audit trail


@dataclass
class Draft:
    account: str
    contact: str
    subject: str
    body: str
    play: str
    prompt_variant: str = "v1"
