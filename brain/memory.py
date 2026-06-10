"""Organ 2 - REMEMBER.

The part every stateless tool skips. One store, one row per account, with the
full history of signals seen, messages sent, and outcomes. Without this, you are
running Mailchimp with prompts. With it, the brain never repeats itself and never
forgets why an account mattered.

SQLite so it runs with zero setup. Swap for Postgres when you outgrow a file.
"""

import json
import sqlite3
import time
from typing import Optional

from .models import Signal


SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    account     TEXT PRIMARY KEY,
    first_seen  REAL,
    last_seen   REAL,
    notes       TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS signals (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    account  TEXT,
    bucket   TEXT,
    summary  TEXT,
    source   TEXT,
    url      TEXT,
    contact  TEXT,
    seen_at  REAL
);
CREATE TABLE IF NOT EXISTS touches (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    account       TEXT,
    contact       TEXT,
    play          TEXT,
    subject       TEXT,
    body          TEXT,
    prompt_variant TEXT,
    sent_at       REAL,
    send_id       TEXT
);
CREATE TABLE IF NOT EXISTS outcomes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    account   TEXT,
    touch_id  INTEGER,
    result    TEXT,          -- replied | meeting | no_reply | bounced | unsub
    bucket    TEXT,          -- which signal bucket triggered the winning touch
    prompt_variant TEXT,
    at        REAL
);
"""


class Memory:
    def __init__(self, path: str = "gtm_brain.db"):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    # --- write side ---------------------------------------------------------

    def record_signal(self, sig: Signal) -> None:
        now = sig.seen_at or time.time()
        self.db.execute(
            "INSERT OR IGNORE INTO accounts(account, first_seen, last_seen) VALUES (?,?,?)",
            (sig.account, now, now),
        )
        self.db.execute(
            "UPDATE accounts SET last_seen=? WHERE account=?", (now, sig.account)
        )
        self.db.execute(
            "INSERT INTO signals(account,bucket,summary,source,url,contact,seen_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (sig.account, sig.bucket, sig.summary, sig.source, sig.url, sig.contact, now),
        )
        self.db.commit()

    def record_touch(self, draft, send_id: str) -> int:
        cur = self.db.execute(
            "INSERT INTO touches(account,contact,play,subject,body,prompt_variant,sent_at,send_id) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (draft.account, draft.contact, draft.play, draft.subject, draft.body,
             draft.prompt_variant, time.time(), send_id),
        )
        self.db.commit()
        return cur.lastrowid

    def record_outcome(self, account: str, touch_id: int, result: str,
                       bucket: str = "", prompt_variant: str = "") -> None:
        self.db.execute(
            "INSERT INTO outcomes(account,touch_id,result,bucket,prompt_variant,at) "
            "VALUES (?,?,?,?,?,?)",
            (account, touch_id, result, bucket, prompt_variant, time.time()),
        )
        self.db.commit()

    # --- read side ----------------------------------------------------------

    def history(self, account: str) -> dict:
        """Everything the brain knows about one account. Fed straight to the judge."""
        signals = [dict(r) for r in self.db.execute(
            "SELECT bucket,summary,seen_at FROM signals WHERE account=? ORDER BY seen_at", (account,))]
        touches = [dict(r) for r in self.db.execute(
            "SELECT play,subject,sent_at FROM touches WHERE account=? ORDER BY sent_at", (account,))]
        outcomes = [dict(r) for r in self.db.execute(
            "SELECT result,bucket,at FROM outcomes WHERE account=? ORDER BY at", (account,))]
        return {"account": account, "signals": signals,
                "touches": touches, "outcomes": outcomes}

    def last_touch_age_days(self, account: str) -> Optional[float]:
        row = self.db.execute(
            "SELECT MAX(sent_at) AS t FROM touches WHERE account=?", (account,)).fetchone()
        if not row or row["t"] is None:
            return None
        return (time.time() - row["t"]) / 86400.0

    def outcome_stats(self) -> dict:
        """Aggregate wins by bucket and by prompt variant. Feeds the learn loop."""
        wins = {"by_bucket": {}, "by_variant": {}}
        for r in self.db.execute(
            "SELECT bucket, prompt_variant, result, COUNT(*) AS n FROM outcomes "
            "GROUP BY bucket, prompt_variant, result"):
            positive = r["result"] in ("replied", "meeting")
            b = wins["by_bucket"].setdefault(r["bucket"] or "?", {"win": 0, "total": 0})
            v = wins["by_variant"].setdefault(r["prompt_variant"] or "?", {"win": 0, "total": 0})
            b["total"] += r["n"]; v["total"] += r["n"]
            if positive:
                b["win"] += r["n"]; v["win"] += r["n"]
        return wins

    def close(self) -> None:
        self.db.close()
