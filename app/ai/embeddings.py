import json

from google import genai

from app.core.config import settings
from app.core.redis import redis_client


client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


async def generate_embedding(
    text: str
):

    clean_text = text.strip()

    if not clean_text:
        return []

    cache_key = (
        f"embedding:{clean_text}"
    )

    cached_embedding = redis_client.get(
        cache_key
    )

    if cached_embedding:

        print(
            f"EMBEDDING CACHE HIT: {cache_key[:60]}"
        )

        return json.loads(
            cached_embedding
        )

    print(
        f"EMBEDDING CACHE MISS: {cache_key[:60]}"
    )

    response = client.models.embed_content(

        model="gemini-embedding-001",

        contents=clean_text
    )

    embedding = (
        response.embeddings[0].values
    )

    redis_client.setex(

        cache_key,

        86400,

        json.dumps(
            embedding
        )
    )

    print(
        f"EMBEDDING STORED: {cache_key[:60]}"
    )

    return embedding