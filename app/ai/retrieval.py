from sqlalchemy import text
from app.ai.embeddings import generate_embedding


STOP_WORDS = {
    "what",
    "is",
    "the",
    "a",
    "an",
    "of",
    "in",
    "to",
    "for",
    "and",
    "with"
}


async def search_similar_chunks(
    db,
    query: str,
    user_id: int,
    limit: int = 5
):

    query_embedding = await generate_embedding(
        query
    )

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

        LIMIT 20

    """)

    results = db.execute(

        sql,

        {
            "embedding": query_embedding,
            "user_id": user_id
        }
    )

    rows = results.fetchall()

    if not rows:
        return []

    query_words = {

        word.lower()

        for word in query.split()

        if word.lower() not in STOP_WORDS

    }

    scored_rows = []

    for row in rows:

        text_words = {

            word.lower().strip(
                ".,:;!?"
            )

            for word in row.chunk_text.split()

        }

        keyword_matches = len(

            query_words.intersection(
                text_words
            )

        )

        final_score = (

            keyword_matches * 10

        ) - row.distance

        scored_rows.append(
            (
                final_score,
                row
            )
        )

    scored_rows.sort(
        key=lambda x: x[0],
        reverse=True
    )

    print("\nQUERY WORDS:")
    print(query_words)

    print("\nRANKED RESULTS:")

    for score, row in scored_rows:

        text_words = {

            word.lower().strip(
                ".,:;!?"
            )

            for word in row.chunk_text.split()

        }

        matches = len(

            query_words.intersection(
                text_words
            )

        )

        print(
            f"NOTE={row.note_id} | "
            f"MATCHES={matches} | "
            f"SCORE={score:.4f} | "
            f"DISTANCE={row.distance:.4f}"
        )

    filtered_rows = [

        row

        for score, row in scored_rows

        if row.distance < 0.45

    ]

    return filtered_rows[:limit]