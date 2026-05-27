import uuid

from supabase import create_client

from app.core.config import settings


supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)


async def upload_note_image(file):

    file_bytes = await file.read()

    filename = (
        f"{uuid.uuid4()}-{file.filename}"
    )

    storage_path = f"notes/{filename}"

    supabase.storage \
        .from_("note-images") \
        .upload(
            storage_path,
            file_bytes,
            {
                "content-type":
                    file.content_type
            }
        )

    public_url = supabase.storage \
        .from_("note-images") \
        .get_public_url(storage_path)

    return public_url