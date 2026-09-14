from contextlib import contextmanager
from threading import RLock
from time import monotonic

from backend.domain.errors import RateLimited


class AttemptLimiter:
    """Single-process limiter; the production command intentionally uses one worker."""

    def __init__(self, clock=monotonic):
        self.clock = clock
        self.entries = {}
        self.lock = RLock()
        self.pending = {}

    @contextmanager
    def attempt(self, keys, maximum=6, window=900):
        # Reserve attempts atomically; never hold this lock across SQL or bcrypt.
        with self.lock:
            self.check(keys, maximum, window)
            for key in keys:
                if self.entries.get(key, (0, 0))[0] + self.pending.get(key, 0) >= maximum:
                    raise RateLimited(1)
            for key in keys:
                self.pending[key] = self.pending.get(key, 0) + 1
        try:
            yield
        finally:
            with self.lock:
                for key in keys:
                    self.pending[key] -= 1
                    if not self.pending[key]:
                        del self.pending[key]

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
