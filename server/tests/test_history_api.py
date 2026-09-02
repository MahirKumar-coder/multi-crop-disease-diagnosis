from fastapi.testclient import TestClient
from app.main import app
from app.services.history_service import history_service

client = TestClient(app)

def test_history_logging_and_retrieval():
    # 1. Clear baseline
    history_service.clear_records()

    # 2. Insert mock diagnostic log
    history_service.log_diagnosis(
        crop="Tomato",
        disease_name="Early Blight",
        confidence=96.4,
        is_confident=True,
        status_flag="VALID_DIAGNOSIS",
        latency_ms=12.5,
        client_ip="127.0.0.1"
    )

    # 3. Test GET /api/history
    response = client.get("/api/history?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_records"] == 1
    record = payload["records"][0]
    assert record["crop"] == "Tomato"
    assert record["disease_name"] == "Early Blight"
    assert record["confidence"] == 96.4
    assert record["is_confident"] is True

    # 4. Test DELETE /api/history
    del_response = client.delete("/api/history")
    assert del_response.status_code == 200
    assert del_response.json()["deleted_count"] == 1

    # 5. Verify empty list
    get_after = client.get("/api/history")
    assert get_after.json()["total_records"] == 0