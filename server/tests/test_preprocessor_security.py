import io
import pytest
from fastapi import UploadFile, HTTPException
from PIL import Image
from app.services.preprocessor import validate_and_preprocess_image

@pytest.mark.asyncio
async def test_valid_jpeg_ingestion():
    # Valid JPEG
    img = Image.new("RGB", (300, 300), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    upload_file = UploadFile(filename="leaf.jpg", file=buf)
    tensor, raw_image = await validate_and_preprocess_image(upload_file)

    assert tensor.shape == (1, 3, 224, 224)
    assert raw_image.size == (300, 300)

@pytest.mark.asyncio
async def test_spoofed_file_extension_rejected():
    # Text file disguised with a .png extension
    fake_png_bytes = b"<?php echo 'malicious payload'; ?>"
    buf = io.BytesIO(fake_png_bytes)
    
    upload_file = UploadFile(filename="shell.png", file=buf)
    
    with pytest.raises(HTTPException) as exc_info:
        await validate_and_preprocess_image(upload_file)

    # Must return HTTP 415 Unsupported Media Type
    assert exc_info.value.status_code == 415

@pytest.mark.asyncio
async def test_corrupted_image_rejected():
    # Invalid image bytes
    buf = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # Broken JPEG header
    upload_file = UploadFile(filename="broken.jpg", file=buf)

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_preprocess_image(upload_file)

    # Must return HTTP 400 Bad Request or HTTP 415
    assert exc_info.value.status_code in [400, 415]