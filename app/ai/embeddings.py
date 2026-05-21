from google import genai

from app.core.config import settings


client = genai.Client(

    api_key=settings.GEMINI_API_KEY
)


async def generate_embedding(text: str):

    clean_text = text.strip()

    if not clean_text:
        return []

    response = client.models.embed_content(

        model="gemini-embedding-001",

        contents=clean_text
    )

    return response.embeddings[0].values