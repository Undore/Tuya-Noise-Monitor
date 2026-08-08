import json
from datetime import datetime, timedelta
from typing import Any

from ascender.common import Injectable
from ascender.core import Service
from redis.asyncio import Redis


@Injectable(provided_in="root")
class RedisStorageService(Service):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def ping(self) -> bool:
        try:
            # noinspection PyUnresolvedReferences
            if await self.redis.ping():
                return True
        except Exception:
            pass

        return False

    def _serialize_value(self, v: Any) -> str:
        if isinstance(v, BaseModel):
            value = v.model_dump_json()
        elif isinstance(v, str):
            return v
        else:
            value = json.dumps(v)

        return value

    async def lpop(self, key: str):
        val = await self.redis.lpop(key)
        if isinstance(val, bytes):
            val = val.decode()

        if val is None:
            return None

        return self._serialize_value(val)

    async def scard(self, key: str) -> int:
        return await self.redis.scard(key)

    async def sadd(self, key: str, value: Any):
        value = self._serialize_value(value)
        return await self.redis.sadd(key, value)

    async def srem(self, key: str, value: Any):
        value = self._serialize_value(value)
        return await self.redis.srem(key, value)

    async def rpush(self, key: str, values: list[Any] | Any):
        if not isinstance(values, list):
            values = [values]

        values = [self._serialize_value(i) for i in values]
        await self.redis.rpush(key, *values)

    async def set(self,
                  key: str,
                  value: Any,
                  ex_at: datetime | None = None,
                  ex: int | timedelta | None = None,
                  nx: bool = False) -> Any:
        value = self._serialize_value(value)
        return await self.redis.set(key, value, exat=ex_at, ex=ex, nx=nx)

    async def set_expires(self, key: str, expires_after: timedelta):
        await self.redis.expire(key, expires_after)

    async def lrange(self, key: str, start: int = 0, end: int = -1):
        return [json.loads(i) for i in await self.redis.lrange(key, start, end)]

    async def get(self, key: str):
        val = await self.redis.get(key)
        return json.loads(val) if val else None

    async def delete(self, key: str):
        await self.redis.delete(key)

    def _safe_load(self, val: bytes):
        try:
            return json.loads(val)
        except Exception:
            return val.decode() if isinstance(val, bytes) else val

    async def list_by_pattern(self, pattern: str) -> dict[str, Any]:
        result = {}

        async for key in self.redis.scan_iter(match=pattern):
            key_str = key.decode() if isinstance(key, bytes) else key
            key_type = await self.redis.type(key)

            if key_type == b"string":
                val = await self.redis.get(key)
                result[key_str] = self._safe_load(val) if val else None

            elif key_type == b"hash":
                val = await self.redis.hgetall(key)
                result[key_str] = {
                    (k.decode() if isinstance(k, bytes) else k): self._safe_load(v)
                    for k, v in val.items()
                }

            elif key_type == b"list":
                val = await self.redis.lrange(key, 0, -1)
                result[key_str] = [self._safe_load(v) for v in val]

            elif key_type == b"set":
                val = await self.redis.smembers(key)
                result[key_str] = [self._safe_load(v) for v in val]

            else:
                result[key_str] = f"<unsupported type: {key_type.decode()}>"

        return result
