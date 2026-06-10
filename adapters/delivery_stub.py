"""A fake delivery engine so you can watch the brain work before it sends anything.

Replace this with the real thing: email (Resend, Postmark), a sequencer, a
LinkedIn tool, a CLI, an internal API. The only contract is
`send(draft, dry_run) -> send_id`.

In --dry-run mode (the default), this just prints. Wire a real engine and pass
dry_run=False from run.py when you actually mean to send.
"""

import time


class StubDelivery:
    def send(self, draft, dry_run: bool = True) -> str:
        send_id = f"stub-{int(time.time()*1000)}"
        header = "DRAFT (dry run, nothing sent)" if dry_run else "SENT"
        print(f"\n--- {header} -> {draft.account} / {draft.contact or 'unknown contact'} ---")
        print(f"play:    {draft.play}  (prompt {draft.prompt_variant})")
        print(f"subject: {draft.subject}")
        print(draft.body)
        print(f"send_id: {send_id}")
        return send_id
