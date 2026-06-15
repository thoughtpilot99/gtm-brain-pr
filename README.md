# gtm-brain

> **This is the lite version. [Max](https://yourmax.ai/en) is the real thing.**
>
> We built Max to solve this exact problem. It turns intent signals into outbound campaigns and runs them across your stack, far beyond what you see here. [Apply for private access →](https://yourmax.ai/en)

A small, open-source skeleton for an **AI GTM brain**: a system that watches buying signals, remembers everything about every account, decides who to act on and why now, drafts outreach grounded in the trigger, and gets smarter every week.

Most "AI SDR" tools are stateless. They send. A brain is different. It is defined by what it **remembers** and what it **learns**, not by how fast it can email.

This repo is not anyone's internal stack. It is a clean, generic version you can clone, wire to your own signal sources and delivery, point at Claude, and run. The architecture is the same one we run in production.

> For humans: UX. For agencies: API. For agents: CLI.
> The brain is the agent layer. You don't click it. You run it.

---

## The five organs

```
          ┌─────────────────────────────────────────────┐
          │                 gtm-brain                    │
          │                                              │
  signals │  1. SENSE    watch Job / Social / Company /  │
 ────────▶│              Funding. start from movement,   │
          │              not from a static list.         │
          │                     │                        │
          │                     ▼                        │
          │  2. REMEMBER  one record per account:        │
          │              every signal, message, reply,   │
          │              outcome. the part tools skip.    │
          │                     │                        │
          │                     ▼                        │
          │  3. JUDGE     Claude reads signal + memory.  │
          │              does it matter? how hot? why    │
          │              now? what is the play?          │
          │                     │                        │
          │                     ▼                        │
          │  4. ACT       draft grounded in the trigger, │
          │              then hand to a delivery engine. │
          │                     │                        │
          │                     ▼                        │
          │  5. LEARN     log the outcome, score the     │
          │              play, keep or kill the prompt.  │
          └─────────────────────────────────────────────┘
                                │
                                ▼
                       outreach + a brain that
                       is smarter next week
```

| Module | Organ | What it does |
|---|---|---|
| `brain/sense.py` | Sense | Pulls signals from a source adapter and normalizes them into the four buckets. |
| `brain/memory.py` | Remember | SQLite store. One row per account, full history of signals / touches / outcomes. |
| `brain/judge.py` | Judge | Asks Claude to score the account and pick the play, using the signal **and** memory. |
| `brain/act.py` | Act | Drafts a message that quotes the trigger back, then calls a delivery adapter. |
| `brain/loop.py` | Learn | Records outcomes, scores plays, and decides which prompt variant to keep. |
| `run.py` | - | The orchestrator that runs sense → judge → act → remember → learn. |
| `prompts/` | - | The two prompts the brain thinks with (`judge.md`, `draft.md`), plus the build prompts that generated each organ (`build-prompts.md`). |

Everything external is a **pluggable adapter** (`adapters/`). The repo ships with stubs that return fake data so you can run the whole loop end to end before you wire anything real.

---

## Quickstart

```bash
git clone https://github.com/nifinet/gtm-brain.git
cd gtm-brain

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # add your ANTHROPIC_API_KEY
# edit config/icp.yaml to describe who actually matters to you

python run.py                 # runs the full loop on stubbed signals, sends nothing
python run.py --offline       # same, but skip the API too (heuristic judge, no key needed)
```

The brain is **safe by default**: it senses, judges, drafts, and remembers, but the delivery adapter only prints. It sends nothing until you pass `--live`, and only once you have wired a real delivery adapter and you mean it.

---

## Wiring it to the real world

The stubs exist so the loop runs on day one. To make it yours, replace two files:

1. **`adapters/signals_stub.py`** → your signal source. Anything that can answer "what moved this week" works: an intent vendor, your CRM, a scraper, product usage, a webhook. Return a list of `Signal` objects in the four buckets.
2. **`adapters/delivery_stub.py`** → your outbound engine. Email, a sequencer, LinkedIn, a CLI. Take a drafted message and an account, send it, return a send id.

Nothing else has to change. `sense` / `remember` / `judge` / `act` / `learn` don't care where signals come from or how a message goes out. That separation is the whole point: the brain is the durable part, the plumbing is swappable.

---

## Configuration

- `config/icp.yaml` - who matters. The brain cannot judge an account without knowing what a good one looks like.
- `config/signals.yaml` - which buckets you watch and how much each is worth as a starting weight (the `learn` loop adjusts these over time).
- `config/sequences.yaml` - the message intents per play (first touch, follow-up, break-up), in plain language. The brain writes the actual copy; this just sets the intent and the guardrails.

## The prompts

The reasoning and the voice live in `prompts/`, in plain files, not buried in code. Edit them to tune the brain to your market without touching Python.

- `prompts/judge.md` - what the judgment layer (organ 3) thinks with. The moat.
- `prompts/draft.md` - what the acting layer (organ 4) writes with. The voice.
- `prompts/build-prompts.md` - the prompts pasted into Claude Code to generate each organ, so you can regenerate or extend any part.

---

## Design principles

1. **Memory first.** If it doesn't remember, it isn't a brain. The store is the center of the repo, not an afterthought.
2. **Listen before you contact.** Every send is triggered by a signal, never by a quota.
3. **Judgment is the moat.** Sending is commodity. Deciding who and why now is not.
4. **The loop is the product.** A version that doesn't get smarter is just a faster script.
5. **Quote the trigger, never "Hi {{firstName}}".** If the message doesn't reference why you reached out now, you skipped the brain.

---

## Status

Reference implementation. Small on purpose. Read it in one sitting, fork it, make it yours.

MIT licensed. PRs welcome.
