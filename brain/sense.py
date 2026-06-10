"""Organ 1 - SENSE.

Pull signals from a source adapter and write them to memory. The brain starts
from movement (something changed at an account), never from a static list you
bought. This is the "stop contacting people, start listening first" layer.

The four buckets:
    job      - new roles, reposted roles, leadership changes
    social   - engagement with you / a competitor, posting about the problem
    company  - launches, expansion, a tech change, a move
    funding  - raises, M&A, new budget

`sense()` is deliberately dumb. It validates and stores. All the judgment about
whether a signal matters happens later, in the judge, where memory is in play.
"""

from typing import List

from .models import Signal
from .memory import Memory


def sense(adapter, memory: Memory) -> List[Signal]:
    """Ask the adapter what moved, validate it, remember it, return it."""
    raw = adapter.fetch()
    fresh: List[Signal] = []
    for sig in raw:
        sig.validate()
        memory.record_signal(sig)
        fresh.append(sig)
    return fresh


def group_by_account(signals: List[Signal]) -> dict:
    """Several signals on one account in one run is itself a signal. Cluster them."""
    out: dict = {}
    for s in signals:
        out.setdefault(s.account, []).append(s)
    return out
