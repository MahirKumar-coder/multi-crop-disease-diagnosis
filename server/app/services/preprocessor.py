import io
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

transforms_pipeline = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

async def validate_and_preprocess_image(file: UploadFile) -> tuple[torch.Tensor, Image.Image]:

    if file.content_type not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file type '{file.content_type}'. Allowed: JPEG, PNG, WEBP."
        )

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image size exceeds max limit of {settings.MAX_UPLOAD_SIZE / (1024 * 1024)}MB."
        )

    try:
        raw_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or invalid image format."
        )

    tensor = transforms_pipeline(raw_image).unsqueeze(0)
    return tensor, raw_image