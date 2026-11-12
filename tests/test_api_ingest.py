import asyncio
from datetime import datetime, timezone
import uuid

from fastapi.testclient import TestClient
import pytest

from app.api.ingest import ingest_queue
from app.main import app
from app.models.raw_event import RawEvent

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_ingest_queue():
    """Đảm bảo hàng đợi trống trước và sau mỗi ca kiểm thử."""
    while not ingest_queue.empty():
        ingest_queue.get_nowait()
    yield
    while not ingest_queue.empty():
        ingest_queue.get_nowait()


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
        uuid.UUID(data["event_id"])
        assert "received_at" in data

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

    def test_tc_ing_016_reject_when_queue_full(self, monkeypatch):
        """TC-ING-016: REST ingest từ chối bản tin với HTTP 503 khi queue đầy."""
        small_queue: asyncio.Queue[RawEvent] = asyncio.Queue(maxsize=2)
        existing_events = [
            RawEvent(
                payload=b"<134>Nov 06 15:00:01 fw-01 %SYS-5-CONFIG: preloaded-1",
                source_ip="10.0.0.1",
                received_at=datetime(2026, 11, 6, 15, 0, 1, tzinfo=timezone.utc),
                channel="api",
            ),
            RawEvent(
                payload=b"<134>Nov 06 15:00:02 fw-01 %SYS-5-CONFIG: preloaded-2",
                source_ip="10.0.0.2",
                received_at=datetime(2026, 11, 6, 15, 0, 2, tzinfo=timezone.utc),
                channel="api",
            ),
        ]
        for ev in existing_events:
            small_queue.put_nowait(ev)

        monkeypatch.setattr("app.api.ingest.ingest_queue", small_queue)

        response = client.post(
            "/api/v1/events/ingest",
            json={
                "raw_message": "<134>Nov 06 15:10:00 fw-01 %SYS-5-CONFIG: overflow-message",
                "source": "REST_CLIENT",
            },
        )

        assert response.status_code == 503
        assert response.json() == {"detail": "Ingest queue is full"}
        assert "SUCCESS" not in response.text
        assert "event_id" not in response.json()

        assert small_queue.qsize() == 2
        drained = [small_queue.get_nowait(), small_queue.get_nowait()]
        assert drained == existing_events


class TestBatchFileImport:
    """Kiểm thử cho Bước 3: Batch Log File Import (Module M1 - BE1 - FR-03)."""

    def test_tc_ing_011_batch_100_valid_lines(self):
        """TC-ING-011: File Log Batch Import - 100 dòng hợp lệ nạp thành công 100%."""
        lines = [f"<134>Nov 06 15:00:00 host-{i:03d} %LINK-3-UPDOWN: Line {i}" for i in range(1, 101)]
        file_content = "\n".join(lines).encode("utf-8")

        response = client.post(
            "/api/v1/events/import-file",
            files={"file": ("batch_100.log", file_content, "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert data["success"] == 100
        assert data["failed"] == 0
        assert data["error_lines"] == []
        assert ingest_queue.qsize() == 100
        first_event = ingest_queue.get_nowait()
        assert first_event.channel == "file"

    def test_tc_ing_012_batch_corrupted_lines(self):
        """TC-ING-012: File Log Batch Import - Trộn lẫn dòng lỗi định dạng (dòng 3 và 7)."""
        raw_lines = [
            b"<134>Nov 06 15:00:00 host-1 %LINK-3-UPDOWN: Line 1",
            b"<134>Nov 06 15:00:00 host-2 %LINK-3-UPDOWN: Line 2",
            b"CORRUPT\x00BINARY\xff\xfeLINE-3",
            b"<134>Nov 06 15:00:00 host-4 %LINK-3-UPDOWN: Line 4",
            b"<134>Nov 06 15:00:00 host-5 %LINK-3-UPDOWN: Line 5",
            b"<134>Nov 06 15:00:00 host-6 %LINK-3-UPDOWN: Line 6",
            b"\x80\x81\x82CORRUPT-LINE-7\x00",
            b"<134>Nov 06 15:00:00 host-8 %LINK-3-UPDOWN: Line 8",
            b"<134>Nov 06 15:00:00 host-9 %LINK-3-UPDOWN: Line 9",
            b"<134>Nov 06 15:00:00 host-10 %LINK-3-UPDOWN: Line 10",
        ]
        file_content = b"\n".join(raw_lines)

        response = client.post(
            "/api/v1/events/import-file",
            files={"file": ("batch_mixed.log", file_content, "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert data["success"] == 8
        assert data["failed"] == 2
        assert data["error_lines"] == [3, 7]
        assert ingest_queue.qsize() == 8

    def test_tc_ing_013_empty_file(self):
        """TC-ING-013: File Log Batch Import - File rỗng 0 byte xử lý an toàn."""
        response = client.post(
            "/api/v1/events/import-file",
            files={"file": ("empty.log", b"", "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["success"] == 0
        assert data["failed"] == 0
        assert data["error_lines"] == []
        assert ingest_queue.empty() is True

    def test_tc_sec_006_path_traversal_protection(self):
        """TC-SEC-006: Kiểm tra chống Path Traversal trên File Import (HTTP 400)."""
        for malicious_name in ["../../../etc/passwd", "..\\..\\secret.log", "dir/sub.log"]:
            response = client.post(
                "/api/v1/events/import-file",
                files={"file": (malicious_name, b"malicious content", "text/plain")},
            )
            assert response.status_code == 400
            assert "Path Traversal" in response.json()["detail"]
