import redis

from app.core.config import settings


try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )
except Exception:
    redis_client = None