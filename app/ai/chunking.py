def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100
):

    if not text:
        return []

    chunks = []

    start = 0

    text_length = len(text)

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end]

        chunk = chunk.strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks