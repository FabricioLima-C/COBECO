from threading import RLock
from time import monotonic

from backend.domain.errors import RateLimited


class AttemptLimiter:
    """Single-process limiter; the production command intentionally uses one worker."""

    def __init__(self, clock=monotonic):
        self.clock = clock
        self.entries = {}
        self.lock = RLock()

    def check(self, keys, maximum=6, window=900):
        now = self.clock()
        with self.lock:
            self.entries = {k: v for k, v in self.entries.items() if v[1] > now}
            for key in keys:
                count, until = self.entries.get(key, (0, now + window))
                if count >= maximum:
                    raise RateLimited(max(1, int(until - now) + 1))

    def fail(self, keys, maximum=6, window=900):
        now = self.clock()
        with self.lock:
            for key in keys:
                count, until = self.entries.get(key, (0, now + window))
                if until <= now:
                    count, until = 0, now + window
                count += 1
                self.entries[key] = (count, now + window if count >= maximum else until)

    def clear(self, key):
        with self.lock:
            self.entries.pop(key, None)

    def request(self, key, maximum=100, window=60):
        with self.lock:
            self.check([key], maximum, window)
            self.fail([key], maximum, window)
