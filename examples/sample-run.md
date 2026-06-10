# Sample run

What you see the first time you run the brain on the shipped stubs.

```bash
$ python run.py --offline
```

```
sensed 5 signals across 4 accounts (prompt variant in use: v1)

[ 60] northwind.io       play=first_touch why_now=raised a 12M Series A two weeks ago

--- DRAFT (dry run, nothing sent) -> northwind.io / VP Sales ---
play:    first_touch  (prompt v1)
subject: about your funding move
Saw that you raised a 12M Series A two weeks ago. That usually means a specific problem is
now on someone's desk. Worth a 15-minute look at how we handle it? Happy to send a
one-pager instead if that's easier.
send_id: stub-1749403200123

[ 20] cendar.co          play=skip       why_now=announced expansion into the DACH region

[ 15] acme-labs.com      play=skip       why_now=their VP Growth posted about cold email reply rates falling

[ 15] quietbrook.com     play=skip       why_now=liked three posts from a direct competitor of ours

acted on 1 of 4 accounts. everything is in memory (gtm_brain.db).

what the brain has learned:

next: feed outcomes back with loop.record_result(...) so the brain learns which
buckets and which copy actually convert.
```

Note what happened:

- **northwind.io** had two signals in one run (a Series A *and* a RevOps role opening). Clustered, that scored highest, so it was the only account the brain acted on.
- The three single-social / single-company accounts were judged **skip**. Saying no is part of the job. A static list would have emailed all four.
- Nothing was sent. The brain is safe by default; it only prints drafts until you pass `--live` with a real delivery adapter wired in.

## Closing the loop

When a reply comes back, tell the brain:

```python
from brain.memory import Memory
from brain import loop

m = Memory("gtm_brain.db")
# touch_id 1 was the northwind first_touch; it booked a meeting off a funding signal
loop.record_result(m, account="northwind.io", touch_id=1,
                   result="meeting", bucket="funding", prompt_variant="v1")

print(loop.report(m))
print("new weights:", loop.adjust_weights(m, {"weights": {"funding": 0.35}}))
```

After enough outcomes, `loop.best_variant(m)` starts returning the prompt that
actually wins, and `adjust_weights` pushes the brain toward the buckets that
convert for *your* market. That is the whole game: the brain you run in month
three is not the brain you cloned in month one.

## Going live

1. Add `ANTHROPIC_API_KEY` to `.env` so the judge and drafting use Claude instead of the heuristic.
2. Replace `adapters/signals_stub.py` with your real signal source.
3. Replace `adapters/delivery_stub.py` with your real outbound engine.
4. Run with `--live` when you mean it. Until then it sends nothing.
