import pytesseract
from PIL import Image
from fastapi import UploadFile
import io


async def extract_text_from_image(file: UploadFile) -> str:
    try:
        contents = await file.read()

        image = Image.open(io.BytesIO(contents))

        text = pytesseract.image_to_string(image)

       # minimal cleanup
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_text = "\n".join(lines[:275]) # limit to first 275 lines

        return clean_text

    except Exception as e:
        raise Exception(f"OCR processing failed: {str(e)}")