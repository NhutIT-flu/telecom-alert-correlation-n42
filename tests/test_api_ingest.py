import uuid
from fastapi.testclient import TestClient

from app.api.ingest import ingest_queue
from app.main import app

client = TestClient(app)


class TestRESTIngestAPI:
    """Kiểm thử cho Bước 1 & Bước 2: REST Ingest API (Module M1 - BE1 - FR-02)."""

    def test_tc_ing_007_valid_rest_ingest(self):
        """TC-ING-007: REST Ingest API hợp lệ tạo sự kiện thành công (HTTP 201)."""
        payload = {
            "raw_message": "<134>Nov 06 15:10:00 fw-01 %SYS-5-CONFIG: Configured from console",
            "source": "REST_CLIENT",
        }
        response = client.post("/api/v1/events/ingest", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert "event_id" in data
        # Kiểm tra event_id là UUID hợp lệ
        uuid.UUID(data["event_id"])
        assert "received_at" in data

        # Kiểm tra event được đưa vào queue đúng chuẩn RawEvent
        assert not ingest_queue.empty()
        event = ingest_queue.get_nowait()
        assert event.payload == payload["raw_message"].encode("utf-8")
        assert event.channel == "api"

    def test_tc_ing_008_missing_required_field(self):
        """TC-ING-008: REST Ingest API - Thiếu trường bắt buộc raw_message (HTTP 422)."""
        response = client.post("/api/v1/events/ingest", json={"source": "REST_CLIENT"})
        assert response.status_code == 422

    def test_tc_ing_009_empty_json_payload(self):
        """TC-ING-009: REST Ingest API - Payload rỗng JSON {} (HTTP 422)."""
        response = client.post("/api/v1/events/ingest", json={})
        assert response.status_code == 422

    def test_tc_ing_010_invalid_content_type(self):
        """TC-ING-010: REST Ingest API - Sai Content-Type (không phải application/json)."""
        response = client.post(
            "/api/v1/events/ingest",
            content="<134>Nov 06 15:10:00 fw-01 test",
            headers={"Content-Type": "text/plain"},
        )
        assert response.status_code == 422

