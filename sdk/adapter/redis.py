"""
redis.py — Base repository for Redis plugins.

Handles JSON serialization/deserialization and optional key prefix.

Usage:
    class SessionRepo(BaseRedisRepository):
        prefix = "session"

    repo = SessionRepo(redis=adapter.client)
    await repo.set("abc123", {"user_id": 42}, ttl=3600)
    session = await repo.get("abc123")
"""

from __future__ import annotations

import json
from abc import ABC
from typing import Any, List, Optional


class BaseRedisRepository(ABC):
    """
    Generic repository for Redis with JSON serialization.

    Set `prefix` on the subclass to namespace all keys automatically.
    Pass a redis-py / aioredis async client as `redis`.
    """

    prefix: str = ""

    def __init__(self, redis: Any) -> None:
        self._redis = redis

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}" if self.prefix else key

    def _serialize(self, value: Any) -> str:
        return json.dumps(value, default=str)

    def _deserialize(self, raw: Any) -> Any:
        if raw is None:
            return None
        return json.loads(raw)

    async def get(self, key: str) -> Optional[Any]:
        raw = await self._redis.get(self._key(key))
        return self._deserialize(raw)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        raw = self._serialize(value)
        if ttl:
            await self._redis.setex(self._key(key), ttl, raw)
        else:
            await self._redis.set(self._key(key), raw)

    async def delete(self, key: str) -> bool:
        return bool(await self._redis.delete(self._key(key)))

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(self._key(key)))

    async def expire(self, key: str, ttl: int) -> None:
        await self._redis.expire(self._key(key), ttl)

    async def ttl(self, key: str) -> int:
        return await self._redis.ttl(self._key(key))

    async def keys(self, pattern: str = "*") -> List[str]:
        full_pattern = f"{self.prefix}:{pattern}" if self.prefix else pattern
        raw_keys = await self._redis.keys(full_pattern)
        return [k.decode() if isinstance(k, bytes) else k for k in raw_keys]

    async def mget(self, keys: List[str]) -> dict[str, Any]:
        full_keys = [self._key(k) for k in keys]
        values = await self._redis.mget(full_keys)
        return {
            k: self._deserialize(v) for k, v in zip(keys, values) if v is not None
        }

    async def mset(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        pipe = self._redis.pipeline()
        for k, v in mapping.items():
            raw = self._serialize(v)
            full_key = self._key(k)
            if ttl:
                pipe.setex(full_key, ttl, raw)
            else:
                pipe.set(full_key, raw)
        await pipe.execute()
