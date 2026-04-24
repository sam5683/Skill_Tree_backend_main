import pytesseract
from PIL import Image
from fastapi import UploadFile, HTTPException
import io
import os
import subprocess
import numpy as np
import cv2

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


async def extract_text_from_image(file: UploadFile) -> str:
    try:
        #1. Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type")

        contents = await file.read()

        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        #2. Load image
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")

        #3. Preprocessing 
        image = image.convert("RGB")  # ensure consistency

        img = np.array(image)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # threshold improves text clarity
        _, img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)

        image = Image.fromarray(img)

        #4. OCR with config (IMPORTANT)
        text = pytesseract.image_to_string(
            image,
            config="--oem 3 --psm 6"
        )

        #5. Clean output
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_text = "\n".join(lines[:275])

        if not clean_text:
            raise HTTPException(status_code=400, detail="No text detected")

        return clean_text

    except HTTPException:
        raise

    except Exception as e:
        print("OCR ERROR:", str(e))
        raise HTTPException(status_code=500, detail="OCR processing failed")