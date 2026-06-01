from app.core.redis import redis_client

print("PING:", redis_client.ping())

redis_client.set(
    "test",
    "hello"
)

print(
    "VALUE:",
    redis_client.get("test")
)