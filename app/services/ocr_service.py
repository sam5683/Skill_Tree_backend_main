import pytesseract
from PIL import Image
from fastapi import UploadFile, HTTPException
import io
import os
import subprocess

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

async def extract_text_from_image(file: UploadFile) -> str:
    try:

        print("PATH CHECK:", os.path.exists("/usr/bin/tesseract"))

        try:
            version = subprocess.check_output(["tesseract", "--version"]).decode()
            print("TESSERACT VERSION:", version)
        except Exception as e:
            print("TESSERACT EXEC ERROR:", str(e))

        contents = await file.read()
        print("FILE SIZE:", len(contents))

        image = Image.open(io.BytesIO(contents))

        text = pytesseract.image_to_string(image)

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines[:275])

    except Exception as e:
        print("OCR ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))