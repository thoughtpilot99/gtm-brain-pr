"""Organ 5 - LEARN.

The feedback loop. The difference between a brain and a script: next week it is
smarter than this week. Log outcomes, score the plays, and let the result move
two dials:

  1. signal bucket weights  - buckets that lead to replies get heavier
  2. prompt variant in use   - the variant with the better win rate is kept

This is the "test, score, keep or kill" loop, expressed as plainly as possible.
Crude math on purpose. The point is that the wiring exists, not that it is fancy.
"""

from .memory import Memory


def record_result(memory: Memory, account: str, touch_id: int, result: str,
                  bucket: str = "", prompt_variant: str = "") -> None:
    """Call this when a reply / meeting / bounce comes back (or from a webhook)."""
    memory.record_outcome(account, touch_id, result, bucket, prompt_variant)


def adjust_weights(memory: Memory, signal_cfg: dict, floor: float = 0.2) -> dict:
    """Re-weight buckets by their win rate. Returns the updated weights."""
    stats = memory.outcome_stats()["by_bucket"]
    weights = dict(signal_cfg.get("weights", {}))
    for bucket, w in list(weights.items()):
        s = stats.get(bucket)
        if not s or s["total"] == 0:
            continue
        win_rate = s["win"] / s["total"]
        # nudge toward win rate, never let a bucket drop below the floor
        weights[bucket] = round(max(floor, 0.5 * w + 0.5 * win_rate), 3)
    return weights


def best_variant(memory: Memory, min_sample: int = 10) -> str:
    """Keep the prompt variant with the best win rate once we have enough data."""
    by_variant = memory.outcome_stats()["by_variant"]
    ranked = []
    for variant, s in by_variant.items():
        if s["total"] >= min_sample:
            ranked.append((s["win"] / s["total"], variant))
    if not ranked:
        return "v1"
    ranked.sort(reverse=True)
    return ranked[0][1]


def report(memory: Memory) -> str:
    """One-glance summary of what the loop has learned so far."""
    stats = memory.outcome_stats()
    lines = ["what the brain has learned:"]
    for bucket, s in sorted(stats["by_bucket"].items()):
        rate = (s["win"] / s["total"] * 100) if s["total"] else 0
        lines.append(f"  {bucket:<8} {s['win']}/{s['total']} wins ({rate:.0f}%)")
    return "\n".join(lines)
