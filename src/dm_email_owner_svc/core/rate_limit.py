import time
import threading
from typing import Dict, Tuple
import logging

class RateLimiter:
    """
    A per-client fixed-window rate limiter.
    Allows up to `limit` requests per `window_size` seconds for each client.
    Thread-safe implementation using threading.Lock.
    """
    def __init__(self, limit: int = 10, window_size: float = 60.0) -> None:
        self.limit = limit
        self.window_size = window_size
        self._clients: Dict[str, Tuple[int, float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a request from the given client_id is allowed under the rate limit.
        Returns True if allowed, False if the limit has been exceeded.
        """
        try:
            with self._lock:
                current_time = time.time()
                count, window_start = self._clients.get(client_id, (0, 0.0))
                # Reset the window if it has expired
                if current_time - window_start >= self.window_size:
                    self._clients[client_id] = (1, current_time)
                    return True
                # Within window and under limit
                if count < self.limit:
                    self._clients[client_id] = (count + 1, window_start)
                    return True
                # Limit exceeded
                return False
        except Exception as e:
            logging.error(e, exc_info=True)
            return False
