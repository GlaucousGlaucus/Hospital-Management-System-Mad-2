from __future__ import annotations

import json
import os
from typing import Any, Optional

import redis


_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(_redis_url, decode_responses=True)
    return _client


def get_cache(key: str) -> Optional[Any]:
    """Return cached JSON value for key, if present."""
    raw = _get_client().get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def set_cache(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Set a JSON-serialised value in cache with TTL."""
    serialized = json.dumps(value, default=str)
    _get_client().setex(key, ttl_seconds, serialized)


def delete_cache(key: str) -> None:
    """Delete a cache key if it exists."""
    _get_client().delete(key)

