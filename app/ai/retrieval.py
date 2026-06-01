from sqlalchemy import text
from app.ai.embeddings import generate_embedding


async def search_similar_chunks(
    db,
    query: str,
    user_id: int,
    limit: int = 5
):

    query_embedding = await generate_embedding(query)

    sql = text("""

        SELECT

            id,
            note_id,
            chunk_text,

            embedding <=> CAST(:embedding AS vector)
            AS distance

        FROM embedding_chunks

        WHERE user_id = :user_id

        ORDER BY embedding <=> CAST(:embedding AS vector)

        LIMIT :limit

    """)

    results = db.execute(

        sql,

        {
            "embedding": query_embedding,
            "user_id": user_id,
            "limit": limit
        }
    )

    rows = results.fetchall()

    filtered_rows = [

        row for row in rows

        if row.distance < 0.45
    ]

    if len(filtered_rows) == 0:
        return []

    return filtered_rows