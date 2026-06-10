"""gtm-brain: a small skeleton for an AI GTM brain.

Five organs:
    sense   - watch the four signal buckets
    memory  - remember every account, signal, touch, outcome
    judge   - Claude decides who is hot, why now, and the play
    act     - draft grounded in the trigger, then deliver
    loop    - log outcomes, score plays, get smarter

The brain is the durable part. Signal sources and delivery are swappable adapters.
"""

from .models import Signal, Verdict, Draft, BUCKETS
from .memory import Memory

__all__ = ["Signal", "Verdict", "Draft", "BUCKETS", "Memory"]
__version__ = "0.1.0"
