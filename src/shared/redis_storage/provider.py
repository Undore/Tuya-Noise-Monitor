from shared.redis_storage.redis_storage_service import RedisStorageService


def provide_redis_storage(storage_url: str):
    if storage_url is None:
        raise RuntimeError("No storage url provided. Redis WILL NOT initialize")

    from redis.asyncio import Redis

    return [{"provide": Redis, "use_factory": lambda: Redis.from_url(storage_url)}, RedisStorageService]
