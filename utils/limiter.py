import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Tuple

try:
    from cachetools import TTLCache
except ImportError:
    TTLCache = None


# Default limits
DEFAULT_RATE_LIMIT_SECONDS = 5
DEFAULT_MAX_REQUESTS_PER_MINUTE = 10
DEFAULT_DAILY_LIMIT = 50
DEFAULT_PREMIUM_DAILY_LIMIT = 200


class RateLimiter:
    """Rate limiter untuk anti-spam"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        if TTLCache:
            self.request_cache = TTLCache(maxsize=10000, ttl=60)
        else:
            self.request_cache = {}

        self.last_request = {}
        self.minute_requests = defaultdict(list)

        # Load from config if available
        try:
            from config import Config
            self.rate_limit_seconds = Config.RATE_LIMIT_SECONDS
            self.max_requests_per_minute = Config.MAX_REQUESTS_PER_MINUTE
        except:
            self.rate_limit_seconds = DEFAULT_RATE_LIMIT_SECONDS
            self.max_requests_per_minute = DEFAULT_MAX_REQUESTS_PER_MINUTE

    def check_rate_limit(self, user_id: int) -> Tuple[bool, int]:
        """Check if user is rate limited"""
        now = time.time()

        last_time = self.last_request.get(user_id, 0)
        time_diff = now - last_time

        if time_diff < self.rate_limit_seconds:
            wait = int(self.rate_limit_seconds - time_diff) + 1
            return False, wait

        minute_ago = now - 60
        user_requests = self.minute_requests[user_id]
        user_requests = [t for t in user_requests if t > minute_ago]
        self.minute_requests[user_id] = user_requests

        if len(user_requests) >= self.max_requests_per_minute:
            oldest = min(user_requests)
            wait = int(60 - (now - oldest)) + 1
            return False, wait

        self.last_request[user_id] = now
        self.minute_requests[user_id].append(now)

        return True, 0

    def reset_user(self, user_id: int):
        """Reset rate limit for user"""
        self.last_request.pop(user_id, None)
        self.minute_requests.pop(user_id, None)


class DailyLimiter:
    """Daily download limiter"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.daily_counts = {}
        self.last_reset = {}

        # Load from config if available
        try:
            from config import Config
            self.daily_limit = Config.DAILY_LIMIT
            self.premium_daily_limit = Config.PREMIUM_DAILY_LIMIT
        except:
            self.daily_limit = DEFAULT_DAILY_LIMIT
            self.premium_daily_limit = DEFAULT_PREMIUM_DAILY_LIMIT

    def _check_reset(self, user_id: int):
        """Check if daily count should be reset"""
        today = datetime.now().date()
        last_reset = self.last_reset.get(user_id)

        if last_reset != today:
            self.daily_counts[user_id] = 0
            self.last_reset[user_id] = today

    def check_daily_limit(self, user_id: int, is_premium: bool = False) -> Tuple[bool, int, int]:
        """Check daily limit"""
        self._check_reset(user_id)

        limit = self.premium_daily_limit if is_premium else self.daily_limit
        current = self.daily_counts.get(user_id, 0)

        if current >= limit:
            return False, current, limit

        return True, current, limit

    def increment(self, user_id: int):
        """Increment daily count"""
        self._check_reset(user_id)
        self.daily_counts[user_id] = self.daily_counts.get(user_id, 0) + 1

    def get_remaining(self, user_id: int, is_premium: bool = False) -> int:
        """Get remaining downloads for today"""
        self._check_reset(user_id)
        limit = self.premium_daily_limit if is_premium else self.daily_limit
        current = self.daily_counts.get(user_id, 0)
        return max(0, limit - current)

    def reset_user(self, user_id: int):
        """Reset daily limit for user"""
        self.daily_counts[user_id] = 0
        self.last_reset[user_id] = datetime.now().date()


# Singleton instances
rate_limiter = RateLimiter()
daily_limiter = DailyLimiter()