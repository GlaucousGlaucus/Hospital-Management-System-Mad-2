from __future__ import annotations

import json
import os
from typing import Any, Optional

import redis
from redis.exceptions import RedisError


_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(_redis_url, decode_responses=True)
    return _client


def get_cache(key: str) -> Optional[Any]:
    """Return cached JSON value for key, if present."""
    try:
        raw = _get_client().get(key)
    except RedisError:
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def set_cache(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Set a JSON-serialised value in cache with TTL."""
    serialized = json.dumps(value, default=str)
    try:
        _get_client().setex(key, ttl_seconds, serialized)
    except RedisError:
        return


def delete_cache_pattern(pattern: str) -> None:
    """Delete all keys matching a Redis pattern."""
    try:
        client = _get_client()
        keys = list(client.scan_iter(match=pattern))
        if keys:
            client.delete(*keys)
    except RedisError:
        return
