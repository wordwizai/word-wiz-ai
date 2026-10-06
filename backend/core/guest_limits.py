"""Abuse limits for the public "try it" (guest) analysis route.

Guest requests cost real money and CPU on every call (ONNX inference on a
small EC2 box, plus Deepgram word timing and Google TTS), and the route has
no account behind it. These limits keep one visitor from running up the bill
or starving signed-in users:

- a per-IP sliding window (short burst limit + daily limit),
- a site-wide hourly cap across all guests,
- a concurrency cap, enforced by the router with an asyncio.Semaphore.

Everything is in memory. That is enough because the backend runs as a single
uvicorn process; counters reset on restart, which only errs toward letting
people in.
"""

import ipaddress
import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """Allow at most `limit` events per `window_seconds` for each key."""

    def __init__(self, limit: int, window_seconds: float, clock=time.monotonic):
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._events: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        """Record an event for `key` if allowed. Returns False when over the limit."""
        now = self._clock()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= self.window:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True

    def prune(self) -> None:
        """Forget keys with no events left in the window."""
        now = self._clock()
        with self._lock:
            for key in list(self._events):
                events = self._events[key]
                while events and now - events[0] >= self.window:
                    events.popleft()
                if not events:
                    del self._events[key]


def client_ip(peer_host: str | None, headers) -> str:
    """The visitor's IP, trusting X-Real-IP only from a private peer.

    In production nginx proxies to uvicorn over the Docker network and sets
    X-Real-IP, so the direct peer is a private address. Port 8443 is also
    reachable directly; a request from a public peer could put anything in
    X-Real-IP, so its header is ignored and the peer address is used.
    """
    peer = peer_host or "unknown"
    try:
        trusted = ipaddress.ip_address(peer).is_private or ipaddress.ip_address(peer).is_loopback
    except ValueError:
        trusted = False
    if trusted:
        forwarded = (headers.get("x-real-ip") or "").strip()
        if forwarded:
            try:
                ipaddress.ip_address(forwarded)
                return forwarded
            except ValueError:
                pass
    return peer


def normalize_sentence(sentence: str) -> str:
    """Normalize a sentence for allowlist comparison (case, quotes, spacing)."""
    s = sentence.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    return " ".join(s.lower().split())
