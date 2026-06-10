#!/usr/bin/env python3
"""The orchestrator. Runs one pass of the brain:

    sense  ->  group by account  ->  judge  ->  act  ->  remember  ->  (learn)

Usage:
    python run.py                    # default-safe: senses, judges, drafts, sends NOTHING
    python run.py --offline          # also skip the API: heuristic judge + template drafts
    python run.py --live             # actually send via your delivery adapter (opt in)

The brain layer is fixed. To make it yours, edit the two adapters and the configs,
not this file.
"""

import argparse
import os
import sys

import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from brain.memory import Memory
from brain.sense import sense, group_by_account
from brain.judge import judge
from brain.act import act
from brain import loop

# --- swap these two lines to point at your real adapters --------------------
from adapters.signals_stub import StubSignals as SignalSource
from adapters.delivery_stub import StubDelivery as DeliverySink
# ----------------------------------------------------------------------------


def load_config(name: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "config", name)
    with open(path) as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Run one pass of the GTM brain.")
    ap.add_argument("--live", action="store_true",
                    help="actually send via the delivery adapter. off by default: "
                         "without this flag the brain drafts but sends nothing")
    ap.add_argument("--offline", action="store_true",
                    help="no API calls: heuristic judge + template drafts")
    ap.add_argument("--limit", type=int, default=0,
                    help="only act on the N hottest accounts this run (0 = no limit)")
    args = ap.parse_args()
    dry_run = not args.live

    if not args.offline and not os.environ.get("ANTHROPIC_API_KEY"):
        print("No ANTHROPIC_API_KEY found. Running --offline (heuristic) instead.\n"
              "Add a key to .env to use Claude for judgment and drafting.\n")
        args.offline = True

    icp = load_config("icp.yaml")
    signal_cfg = load_config("signals.yaml")
    sequences = load_config("sequences.yaml")

    memory = Memory(os.environ.get("GTM_BRAIN_DB", "gtm_brain.db"))
    signals_in = SignalSource()
    delivery = DeliverySink()
    variant = loop.best_variant(memory)

    # 1. SENSE
    fresh = sense(signals_in, memory)
    by_account = group_by_account(fresh)
    print(f"sensed {len(fresh)} signals across {len(by_account)} accounts "
          f"(prompt variant in use: {variant})")

    # 2. JUDGE every account
    verdicts = []
    for account, sigs in by_account.items():
        v = judge(account, sigs, icp, memory, offline=args.offline)
        verdicts.append((v, sigs))

    # rank hottest first; optionally cap how many we act on
    verdicts.sort(key=lambda x: x[0].score, reverse=True)
    if args.limit:
        verdicts = verdicts[: args.limit]

    # 3. ACT on the ones worth acting on
    acted = 0
    for v, sigs in verdicts:
        # the trigger is the heaviest signal; the contact is the best one on the
        # account, even if it came from a different signal in the cluster
        trigger = max(sigs, key=lambda s: signal_cfg.get("weights", {}).get(s.bucket, 0))
        trigger.contact = trigger.contact or next((s.contact for s in sigs if s.contact), "")
        print(f"\n[{v.score:>3}] {v.account:<18} play={v.play:<11} why_now={v.why_now}")
        touch_id = act(v, trigger, sequences, delivery, memory,
                       dry_run=dry_run, offline=args.offline,
                       prompt_variant=variant)
        if touch_id:
            acted += 1

    print(f"\nacted on {acted} of {len(verdicts)} accounts. "
          f"everything is in memory ({os.environ.get('GTM_BRAIN_DB', 'gtm_brain.db')}).")
    print("\n" + loop.report(memory))
    print("\nnext: feed outcomes back with loop.record_result(...) so the brain "
          "learns which buckets and which copy actually convert.")
    memory.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
