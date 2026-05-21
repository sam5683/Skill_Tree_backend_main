# app/ai/client.py

import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


async def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.3,
):

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.post(
                GROQ_URL,
                headers=headers,
                json=data,
            )

        response.raise_for_status()

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        logger.error("LLM timeout")
        return None

    except httpx.HTTPStatusError as e:
        logger.error(f"LLM HTTP error: {e.response.text}")
        return None

    except Exception as e:
        logger.error(f"Unexpected LLM error: {str(e)}")
        return None