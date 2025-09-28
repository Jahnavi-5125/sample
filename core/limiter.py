# limiter.py

import time
from fastapi import HTTPException
from src.backend.utils.api_utils import RedisManager


class AsyncRateLimiter:
    _instance = None
    enable: bool = True  # Class-level toggle

    def __new__(cls, redis_manager: RedisManager):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, redis_manager: RedisManager):
        if not hasattr(self, "_initialized"):
            self.redis = redis_manager
            self.rate_configs = {
                "standard": (10, 60),
                "strict": (2, 60),
                "relaxed": (100, 60),
                "free": None
            }
            self._initialized = True

    @classmethod
    def set_enable(cls, value: bool):
        cls.enable = value

    def _make_key(self, user_id: str, route_name: str):
        return f"ratelimit:{route_name}:{user_id}"

    async def check_rate_limit(self, user_id: str, route_name: str, limit_key: str):
        if not self.enable or self.rate_configs.get(limit_key) is None:
            return

        if limit_key not in self.rate_configs:
            raise HTTPException(status_code=500, detail="Invalid rate limit key")

        max_requests, window_sec = self.rate_configs[limit_key]
        redis_key = self._make_key(user_id, route_name)

        try:
            count = await self.redis.safe_execute("incr", redis_key)
            if int(count) == 1:
                await self.redis.safe_execute("expire", redis_key, window_sec)
        except Exception:
            raise HTTPException(status_code=500, detail="Rate limiter failed")

        if int(count) > max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {max_requests} requests per {window_sec} seconds"
            )
