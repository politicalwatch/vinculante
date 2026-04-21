from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from vinculante.infrastructure.config.settings import get_settings


async def init_cache() -> None:
    settings = get_settings()
    redis = aioredis.from_url(settings.cache_redis_host)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
