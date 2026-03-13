"""
API限流器 - 控制资源使用
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import time


class RateLimitScope(Enum):
    GLOBAL = "global"
    AGENT = "agent"
    USER = "user"


@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000
    scope: RateLimitScope = RateLimitScope.AGENT


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[float] = None


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
    
    async def acquire(self, tokens: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    @property
    def available(self) -> float:
        now = time.monotonic()
        elapsed = now - self.last_refill
        return min(self.capacity, self.tokens + elapsed * self.refill_rate)


class SlidingWindowCounter:
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.requests: list = []
    
    async def acquire(self) -> bool:
        now = time.monotonic()
        self.requests = [t for t in self.requests if now - t < self.window_size]
        self.requests.append(now)
        return True
    
    @property
    def count(self) -> int:
        now = time.monotonic()
        self.requests = [t for t in self.requests if now - t < self.window_size]
        return len(self.requests)


class APIRateLimiter:
    def __init__(self, default_config: Optional[RateLimitConfig] = None):
        self.default_config = default_config or RateLimitConfig()
        self._buckets: Dict[str, TokenBucket] = {}
        self._counters: Dict[str, SlidingWindowCounter] = {}
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self, key: str, config: Optional[RateLimitConfig] = None) -> RateLimitResult:
        config = config or self.default_config
        async with self._lock:
            bucket_key = f"{key}:tokens"
            if bucket_key not in self._buckets:
                self._buckets[bucket_key] = TokenBucket(
                    capacity=config.tokens_per_minute,
                    refill_rate=config.tokens_per_minute / 60.0
                )
            bucket = self._buckets[bucket_key]
            if not await bucket.acquire(1):
                return RateLimitResult(False, int(bucket.available), datetime.now() + timedelta(seconds=60), 1.0)
            counter_key = f"{key}:requests"
            if counter_key not in self._counters:
                self._counters[counter_key] = SlidingWindowCounter(60)
            counter = self._counters[counter_key]
            await counter.acquire()
            if counter.count > config.requests_per_minute:
                return RateLimitResult(False, 0, datetime.now() + timedelta(seconds=60), 60.0 / config.requests_per_minute)
            return RateLimitResult(True, config.requests_per_minute - counter.count, datetime.now() + timedelta(seconds=60))
    
    async def consume_tokens(self, key: str, tokens: int, capacity: int = 100000) -> bool:
        async with self._lock:
            bucket_key = f"{key}:tokens"
            if bucket_key not in self._buckets:
                self._buckets[bucket_key] = TokenBucket(capacity, capacity / 60.0)
            return await self._buckets[bucket_key].acquire(tokens)
    
    async def reset(self, key: str):
        async with self._lock:
            self._buckets.pop(f"{key}:tokens", None)
            self._counters.pop(f"{key}:requests", None)
    
    def get_statistics(self) -> Dict:
        return {
            "active_buckets": len(self._buckets),
            "active_counters": len(self._counters),
            "default_rpm": self.default_config.requests_per_minute,
        }
