import hashlib
from app.ai.client import call_llm
from app.ai.retrieval import search_similar_chunks
from app.core.redis import redis_client


async def rag_answer(db, query: str, user_id: int):

    normalized_query = query.strip().lower()

    cache_key = "rag:" + str(user_id) + ":" + hashlib.md5(normalized_query.encode()).hexdigest()

    cached_answer = redis_client.get(cache_key)

    if cached_answer:
        print(f"REDIS HIT: {cache_key}")
        return {"answer": cached_answer, "sources": []}

    # FIX: Moved outside the IF block so it executes on a true cache miss
    print(f"REDIS MISS: {cache_key}")

    results = await search_similar_chunks(
        db=db, query=normalized_query, user_id=user_id, limit=3
    )

    if not results:

        prompt = f"""
You are Pepa.

An AI mentor inside SkillTree.

Answer using your general knowledge.

Be:
- Direct
- Accurate
- Logical
- Concise

If you are uncertain, say so.

QUESTION:

{query}

ANSWER:
"""

        answer = await call_llm(
            prompt=prompt,
            temperature=0.3
        )

        redis_client.setex(
            cache_key,
            300,
            answer
        )

        return {
            "answer": answer,
            "sources": []
        }
    
    # ========================================
    # NEW CODE: MEASURING VECTOR DISTANCE
    # ========================================
    best_distance = results[0].distance

    print(f"BEST DISTANCE: {best_distance}")
    # ========================================

    context = "\n\n".join( [row.chunk_text for row in results])

    prompt = f"""
You are Pepa.

An AI mentor inside SkillTree.

Your goal is to help users learn accurately and think clearly.

========================
RULES
========================

1. Use the provided note context first.

2. If the answer exists in the context:
   answer directly.

3. Do not invent facts.

4. Do not guess.

5. Do not speculate.

6. If the answer is not present in the context:
   use general knowledge only when it is clearly unrelated to the user's notes.

7. If the question appears to be asking about information stored in notes and the information is missing:
   say:

   "I could not find that information in your notes."

8. Do not confuse similar terms.

Example:

deployment code ≠ development code

backup access code ≠ backup server

secret access code ≠ deployment code

9. Prefer the exact wording found in the notes.

========================
ANSWER STYLE
========================

- Short
- Direct
- Precise
- Logical

For factual questions:

Answer in 1-3 sentences.

For conceptual questions:

Explain clearly using simple language.

Do not add unnecessary information.

========================
CONTEXT
========================

{context}

========================
QUESTION
========================

{query}

========================
ANSWER
========================
"""
    response = await call_llm(prompt=prompt, temperature=0.1)

    if response:
        redis_client.setex(cache_key, 3600, response)
        print(f"STORED IN REDIS: {cache_key}")

    return {
        "answer": response,
        "sources": [
            {"note_id": row.note_id, "chunk_text": row.chunk_text} for row in results
        ],
    }