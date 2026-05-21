from app.ai.retrieval import search_similar_chunks

from app.ai.client import call_llm


async def rag_answer(

    db,

    query: str,

    user_id: int
):

    results = search_similar_chunks(

        db=db,

        query=query,

        user_id=user_id,

        limit=5
    )

    context = "\n\n".join(

        [row.chunk_text for row in results]
    )

    prompt = f"""

You are a retrieval-augmented AI assistant.

Answer the user's question using ONLY
the provided context.

Use the provided context to answer the question.

If the context is partially relevant,
answer as best as possible while staying grounded in the context.

Do not invent facts outside the context.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

    response = await call_llm(prompt)

    return {

        "answer": response,

        "sources": [

            {
                "note_id": row.note_id,
                "chunk_text": row.chunk_text
            }

            for row in results
        ]
    }