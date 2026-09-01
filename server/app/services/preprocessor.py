import io
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import torch
from torchvision import transforms
import puremagic
from app.core.config import settings
from app.core.logger import logger

# ---------------------------------------------------------------------------
# Security Configuration Constants
# ---------------------------------------------------------------------------
ALLOWED_MIME_TYPES = {
    "image/jpeg": ["jpeg", "jpg"],
    "image/png": ["png"],
    "image/webp": ["webp"]
}

# 1. Enforce Pillow pixel limit to prevent Decompression Bomb (DoS attacks)
# Restricts maximum image to ~25 Megapixels (e.g., 5000 x 5000)
Image.MAX_IMAGE_PIXELS = 25_000_000

# 2. Maximum payload memory buffer (10 MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# 3. ImageNet Normalization Pipeline
PREPROCESS_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def validate_magic_bytes(file_header_bytes: bytes) -> str:
    """
    Validates genuine binary file signatures (magic bytes) to prevent
    attackers from uploading malicious scripts with spoofed .jpg/.png extensions.
    """
    try:
        # Detect true MIME type directly from the file header stream
        matches = puremagic.magic_string(file_header_bytes)
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported or unrecognized file binary format. Only genuine JPEG, PNG, or WebP images are permitted."
            )
        
        detected_mime = matches[0].mime_type
        if detected_mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Security check failed: Uploaded binary matches '{detected_mime}', but only JPEG, PNG, and WebP are allowed."
            )
        return detected_mime
    except puremagic.PureError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Corrupted file header: Unable to verify valid image magic bytes."
        )


async def validate_and_preprocess_image(file: UploadFile) -> Tuple[torch.Tensor, Image.Image]:
    """
    Hardened ingestion pipeline performing:
    1. Stream size checks (enforces memory limit)
    2. Deep magic-byte binary header verification (HTTP 415)
    3. Safe decompression with Pillow pixel bounds (HTTP 400)
    4. PyTorch ImageNet tensor normalization (1, 3, 224, 224)
    """
    # 1. Read byte stream and check memory boundary
    contents = await file.read()
    file_size = len(contents)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file payload is empty."
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file size ({file_size / (1024*1024):.2f}MB) exceeds the maximum allowed limit of 10MB."
        )

    # 2. Magic-byte signature verification (inspect first 2048 bytes)
    validate_magic_bytes(contents[:2048])

    # 3. Decode & Safely Decompress Image with Pillow
    try:
        image_stream = io.BytesIO(contents)
        raw_image = Image.open(image_stream)
        
        # Verify Pillow recognizes image structure without full decompression
        raw_image.verify()
        
        # Re-open stream since verify() exhausts the byte pointer
        image_stream.seek(0)
        raw_image = Image.open(image_stream).convert("RGB")
        
    except Image.DecompressionBombError:
        logger.warning(f"Decompression Bomb attempt blocked from uploaded image: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image dimensions exceed maximum security threshold (possible decompression bomb)."
        )
    except Exception as e:
        logger.error(f"Image decode error on file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file content is corrupted and cannot be decoded into a valid image."
        )

    # 4. Transform to Normalized PyTorch Tensor (1, 3, 224, 224)
    tensor = PREPROCESS_TRANSFORM(raw_image).unsqueeze(0)

    return tensor, raw_image