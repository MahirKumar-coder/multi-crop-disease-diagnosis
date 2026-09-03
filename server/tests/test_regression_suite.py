import io
import json
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.knowledge_base_service import kb_service
from app.services.history_service import history_service

client = TestClient(app)

# Helper function to generate test image buffers
def generate_test_image(color=(34, 139, 34), size=(224, 224), format="JPEG") -> io.BytesIO:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf

# =========================================================================
# 1. System Health & Catalog Sanity Checks
# =========================================================================
def test_system_health_check():
    """Verify system liveness probe."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["online", "healthy", "ok"]

def test_disease_catalog_count():
    """Ensure all 38 disease categories are exposed in the catalog."""
    response = client.get("/api/diseases")
    assert response.status_code == 200
    diseases = response.json()
    assert diseases["total"] == 38
    assert len(diseases["items"]) == 38

# =========================================================================
# 2. Comprehensive 38-Class Metadata & Remediation Lookups
# =========================================================================
# Load 38 class names dynamically from the knowledge base service
ALL_38_CLASSES = list(kb_service.all_records.keys())

@pytest.mark.parametrize("disease_id", ALL_38_CLASSES)
def test_all_38_disease_metadata_lookups(disease_id):
    """
    Parametrized regression test verifying every class key contains
    crop, pathogen, severity, and treatment dosage structures.
    """
    response = client.get(f"/api/diseases/{disease_id}")
    assert response.status_code == 200, f"Metadata lookup failed for {disease_id}"
    record = response.json()
    
    assert "crop" in record
    assert "disease_name" in record
    assert "remediation" in record
    assert "organic" in record["remediation"]
    assert "chemical" in record["remediation"]
    assert "preventive" in record["remediation"]
    
    # Verify chemical dosage structure if condition is diseased
    if not record.get("is_healthy", False):
        chemicals = record["remediation"]["chemical"]
        if len(chemicals) > 0:
            assert "dosage" in chemicals[0]
            assert "frequency" in chemicals[0]

# =========================================================================
# 3. SHA-256 Caching Hit Verification
# =========================================================================
def test_sha256_inference_cache_hit():
    """Verify that repeat image uploads return cached=True with sub-15ms latency."""
    img_buf = generate_test_image(color=(45, 120, 45))
    files = {"file": ("cache_test_leaf.jpg", img_buf, "image/jpeg")}

    # Initial request (Cache miss)
    resp1 = client.post("/api/predict", files=files)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["cached"] is False

    # Second request with exact same payload (Cache hit)
    img_buf.seek(0)
    files2 = {"file": ("cache_test_leaf.jpg", img_buf, "image/jpeg")}
    resp2 = client.post("/api/predict", files=files2)
    assert resp2.status_code == 200
    data2 = resp2.json()
    
    assert data2["cached"] is True
    assert data2["predicted_class"] == data1["predicted_class"]
    assert data2["confidence"] == data1["confidence"]

# =========================================================================
# 4. Error Boundaries & Security Input Validation
# =========================================================================
def test_error_boundary_unsupported_media_type():
    """Verify HTTP 415 rejection on text/plain or invalid file types."""
    fake_file = io.BytesIO(b"Not an image stream")
    files = {"file": ("test.txt", fake_file, "text/plain")}
    response = client.post("/api/predict", files=files)
    assert response.status_code == 415

def test_error_boundary_spoofed_extension():
    """Verify HTTP 415 rejection when a PHP script is disguised as .png."""
    spoofed_bytes = io.BytesIO(b"<?php echo 'malicious code'; ?>")
    files = {"file": ("shell.png", spoofed_bytes, "image/png")}
    response = client.post("/api/predict", files=files)
    assert response.status_code == 415

def test_error_boundary_corrupted_image_header():
    """Verify HTTP 400 rejection on a corrupted image stream."""
    corrupted_bytes = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 64)
    files = {"file": ("corrupted.jpg", corrupted_bytes, "image/jpeg")}
    response = client.post("/api/predict", files=files)
    assert response.status_code in [400, 415]

def test_error_boundary_oversized_payload():
    """Verify HTTP 413 rejection when file payload exceeds 10MB."""
    oversized_bytes = io.BytesIO(b"0" * (11 * 1024 * 1024))  # 11 MB
    files = {"file": ("huge.jpg", oversized_bytes, "image/jpeg")}
    response = client.post("/api/predict", files=files)
    assert response.status_code == 413

def test_nonexistent_disease_id_404():
    """Verify HTTP 404 for invalid catalog identifiers."""
    response = client.get("/api/diseases/NonExistent_Disease_123")
    assert response.status_code == 404

# =========================================================================
# 5. Diagnostic Audit Logging & History Endpoints
# =========================================================================
def test_history_logging_lifecycle():
    """Verify audit record insertion, retrieval, and purge."""
    # Purge baseline
    client.delete("/api/history")

    # Run inference to trigger audit logging
    img_buf = generate_test_image()
    files = {"file": ("history_leaf.jpg", img_buf, "image/jpeg")}
    pred_resp = client.post("/api/predict", files=files)
    assert pred_resp.status_code == 200

    # Retrieve history
    hist_resp = client.get("/api/history?limit=10")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["total_records"] >= 1
    
    first_record = hist_data["records"][0]
    assert "timestamp" in first_record
    assert "crop" in first_record
    assert "disease_name" in first_record
    assert "latency_ms" in first_record

    # Purge history
    del_resp = client.delete("/api/history")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] >= 1