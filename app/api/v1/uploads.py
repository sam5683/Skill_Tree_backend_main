from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends

from app.core.security import get_current_user
from app.models.user import User

from app.services.storage_service import (
    upload_note_image
)

router = APIRouter(
    prefix="/uploads",
    tags=["uploads"]
)


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):

    image_url = await upload_note_image(
        file
    )

    return {
        "url": image_url
    }