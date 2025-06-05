from redis import Redis
from app.core.config import settings

class RedisCacheService:
    def __init__(self):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

    async def get(self, key: str) -> str:
        return self.redis.get(key)

    async def set(self, key: str, value: str, expire: int = None) -> None:
        self.redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        return self.redis.exists(key) == 1