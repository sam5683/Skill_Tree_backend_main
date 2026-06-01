from fastapi import HTTPException

from app.core.redis import redis_client


async def check_rate_limit(
    user_id: int,
    limit: int = 15,
    window: int = 60
):

    key = f"rate_limit:{user_id}"

    current = redis_client.incr(key)

    if current == 1:

        redis_client.expire(
            key,
            window
        )

    if current > limit:

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )