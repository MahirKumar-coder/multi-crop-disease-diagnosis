import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app

client = TestClient(app)

def create_test_image(color=(34, 139, 34)):
    img = Image.new("RGB", (224, 224), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf

def test_predict_schema_contains_calibration_fields():
    """Verify presence of is_confident, status_flag, and warning_message in response."""
    img_buf = create_test_image()
    files = {"file": ("leaf.jpg", img_buf, "image/jpeg")}
    
    response = client.post("/api/predict", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert "is_confident" in data
    assert "status_flag" in data
    assert "warning_message" in data
    assert isinstance(data["is_confident"], bool)
    assert data["status_flag"] in ["VALID_DIAGNOSIS", "UNKNOWN_OR_AMBIGUOUS_SCAN"]
    
    if not data["is_confident"]:
        assert data["warning_message"] is not None
        assert "Low confidence" in data["warning_message"]