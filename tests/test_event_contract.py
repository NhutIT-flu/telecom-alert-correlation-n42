"""Bộ kiểm thử xác thực Hợp đồng API và DTO Sự kiện v1.0.0 (N42-62).

Căn cứ:
  - docs/N42-62_DESIGN.md
  - docs/openapi-v1.yaml
  - app/schemas/event_contract.py
  - tests/fixtures/contract_v1/
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.models.alert_event import AlertEvent
from app.schemas.event_contract import (
    CONTRACT_VERSION,
    EventIngestBatchRequest,
    EventIngestRequest,
    EventIngestResponse,
    EventListQuery,
    EventListResponse,
    EventLocatorQuery,
    EventView,
    decode_cursor,
    encode_cursor,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures" / "contract_v1"
OPENAPI_PATH = ROOT_DIR / "docs" / "openapi-v1.yaml"


def test_event_view_from_fixture() -> None:
    """Xác thực DTO EventView đọc thành công từ fixture JSON mẫu."""
    fixture_file = FIXTURES_DIR / "event_view_sample.json"
    assert fixture_file.exists(), f"Không tìm thấy fixture: {fixture_file}"

    data = json.loads(fixture_file.read_text(encoding="utf-8"))
    view = EventView.model_validate(data)

    assert view.id == uuid.UUID("e0b0e5d4-4f0f-4886-b47a-c71c4c92b23a")
    assert view.hostname == "r-core-01"
    assert view.severity == 3
    assert view.severity_label == "ERROR"
    assert view.vendor == "cisco"
    assert view.program == "LINK"
    assert view.mnemonic == "UPDOWN"
    assert view.parse_status == "parsed"


def test_event_view_from_alert_event() -> None:
    """Xác thực chuyển đổi tự động từ AlertEvent sang EventView."""
    now = datetime.now(timezone.utc)
    alert = AlertEvent(
        id=uuid.uuid4(),
        received_at=now,
        event_timestamp=now,
        source_ip="192.0.2.10",
        hostname="sw-dist-01",
        facility=16,
        severity=2,
        vendor="huawei",
        program="ENTITYRES",
        mnemonic="POWER_FAIL",
        message="Power module 1 failure",
        raw_payload="<130>Nov 16 sw-dist-01 Power module 1 failure",
    )

    view = EventView.from_alert_event(alert)

    assert view.id == alert.id
    assert view.hostname == alert.hostname
    assert view.severity == 2
    assert view.severity_label == "CRITICAL"
    assert view.vendor == "huawei"
    assert view.program == "ENTITYRES"
    assert not hasattr(view, "raw_payload") or "raw_payload" not in view.model_fields


def test_event_ingest_request_valid() -> None:
    """Xác thực Request Ingest đơn lẻ hợp lệ từ fixture."""
    fixture_file = FIXTURES_DIR / "ingest_request_single.json"
    data = json.loads(fixture_file.read_text(encoding="utf-8"))

    req = EventIngestRequest.model_validate(data)
    assert "%LINK-3-UPDOWN" in req.raw_message
    assert req.source_ip == "192.0.2.1"


def test_event_ingest_request_validation_errors() -> None:
    """Xác thực bắt lỗi schema khi dữ liệu Ingest không hợp lệ."""
    with pytest.raises(ValidationError):
        EventIngestRequest(raw_message="")

    with pytest.raises(ValidationError):
        EventIngestRequest(raw_message="<134>test", source_ip="not-an-ip")


def test_event_ingest_batch_request() -> None:
    """Xác thực tiếp nhận lô bản tin cảnh báo (Batch Ingest)."""
    fixture_file = FIXTURES_DIR / "ingest_request_batch.json"
    data = json.loads(fixture_file.read_text(encoding="utf-8"))

    batch_req = EventIngestBatchRequest.model_validate(data)
    assert len(batch_req.items) == 2
    assert batch_req.items[0].source_ip == "192.0.2.1"
    assert batch_req.items[1].source_ip == "192.0.2.2"


def test_event_ingest_responses() -> None:
    """Xác thực cả hai dạng response: bền vững (persisted) và hàng đợi (queued)."""
    durable_data = json.loads((FIXTURES_DIR / "ingest_response_durable.json").read_text(encoding="utf-8"))
    durable_resp = EventIngestResponse.model_validate(durable_data)
    assert durable_resp.status == "persisted"
    assert durable_resp.event_id is not None
    assert durable_resp.receipt_id is None

    queued_data = json.loads((FIXTURES_DIR / "ingest_response_queued.json").read_text(encoding="utf-8"))
    queued_resp = EventIngestResponse.model_validate(queued_data)
    assert queued_resp.status == "queued"
    assert queued_resp.receipt_id is not None
    assert queued_resp.event_id is None


def test_event_ingest_response_rejects_missing_ack_id() -> None:
    """Từ chối ACK persisted thiếu event_id và ACK queued thiếu receipt_id."""
    with pytest.raises(ValidationError, match="event_id is required"):
        EventIngestResponse(status="persisted", event_id=None)

    with pytest.raises(ValidationError, match="receipt_id is required"):
        EventIngestResponse(status="queued", receipt_id=None)

    with pytest.raises(ValidationError, match="timezone-aware"):
        EventIngestResponse(
            status="persisted",
            event_id=uuid.uuid4(),
            received_at=datetime(2026, 11, 16, 7, 0, 0),
        )


def test_event_list_query_from_to_and_validation() -> None:
    """Xác thực tham số from/to đồng nhất OpenAPI, từ chối datetime thiếu múi giờ và khoảng thời gian đảo."""
    # 1. Hợp lệ với alias OpenAPI 'from' / 'to'
    valid_query = EventListQuery.model_validate(
        {
            "from": "2026-11-16T07:00:00Z",
            "to": "2026-11-16T08:00:00Z",
            "hostname": "r-core-01",
            "limit": 50,
        }
    )
    assert valid_query.from_time == datetime(2026, 11, 16, 7, 0, 0, tzinfo=timezone.utc)
    assert valid_query.to_time == datetime(2026, 11, 16, 8, 0, 0, tzinfo=timezone.utc)

    # 2. Từ chối datetime thiếu múi giờ (naive datetime)
    with pytest.raises(ValidationError, match="timezone-aware"):
        EventListQuery.model_validate(
            {
                "from": "2026-11-16T07:00:00",
                "to": "2026-11-16T08:00:00Z",
            }
        )

    with pytest.raises(ValidationError, match="timezone-aware"):
        EventListQuery(
            from_time=datetime(2026, 11, 16, 7, 0, 0, tzinfo=timezone.utc),
            to_time=datetime(2026, 11, 16, 8, 0, 0),
        )

    # 3. Từ chối khoảng thời gian đảo (from > to)
    with pytest.raises(ValidationError, match="less than or equal"):
        EventListQuery.model_validate(
            {
                "from": "2026-11-16T09:00:00Z",
                "to": "2026-11-16T08:00:00Z",
            }
        )


def test_event_locator_query_matches_n42_16() -> None:
    """Xác thực EventLocatorQuery yêu cầu event_timestamp có múi giờ để định vị cặp khóa (id, event_timestamp)."""
    valid_loc = EventLocatorQuery.model_validate({"event_timestamp": "2026-11-16T07:15:30Z"})
    assert valid_loc.event_timestamp.tzinfo == timezone.utc

    with pytest.raises(ValidationError, match="timezone-aware"):
        EventLocatorQuery(event_timestamp=datetime(2026, 11, 16, 7, 15, 30))


def test_event_list_response() -> None:
    """Xác thực Response danh sách sự kiện trả về cho Dashboard."""
    fixture_file = FIXTURES_DIR / "event_list_response.json"
    data = json.loads(fixture_file.read_text(encoding="utf-8"))

    resp = EventListResponse.model_validate(data)
    assert len(resp.items) == 1
    assert resp.has_more is True
    assert resp.next_cursor is not None
    assert resp.total_matched == 1


def test_cursor_encode_decode_roundtrip() -> None:
    """Xác thực tính toàn vẹn 100% khi mã hóa và giải mã con trỏ phân trang (Cursor)."""
    original_id = uuid.uuid4()
    original_ts = datetime(2026, 11, 16, 7, 30, 0, 123456, tzinfo=timezone.utc)

    cursor_str = encode_cursor(original_ts, original_id)
    assert isinstance(cursor_str, str)
    assert len(cursor_str) > 0

    decoded_ts, decoded_id = decode_cursor(cursor_str)
    assert decoded_id == original_id
    assert decoded_ts == original_ts


def test_cursor_decode_invalid_and_naive() -> None:
    """Xác thực từ chối cursor hỏng hoặc timestamp thiếu múi giờ."""
    with pytest.raises(ValueError, match="timezone-aware"):
        encode_cursor(datetime(2026, 11, 16, 7, 30, 0), uuid.uuid4())

    with pytest.raises(ValueError, match="Invalid pagination cursor"):
        decode_cursor("not-a-valid-base64-string!!!")

    with pytest.raises(ValueError, match="Invalid pagination cursor"):
        decode_cursor("SGVsbG8gV29ybGQ=")


def test_openapi_schema_and_version_parity() -> None:
    """Xác nhận OpenAPI, Pydantic CONTRACT_VERSION và tham số from/to/locator đồng bộ cùng phiên bản 1.0.0."""
    assert OPENAPI_PATH.exists(), f"Không tìm thấy tệp OpenAPI: {OPENAPI_PATH}"
    spec = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))

    assert spec["info"]["version"] == CONTRACT_VERSION == "1.0.0"

    # Kiểm tra GET /api/v1/events dùng đúng 'from' và 'to'
    list_params = {p["name"]: p for p in spec["paths"]["/api/v1/events"]["get"]["parameters"]}
    assert "from" in list_params and list_params["from"]["required"] is True
    assert "to" in list_params and list_params["to"]["required"] is True
    assert "from_time" not in list_params and "to_time" not in list_params

    # Kiểm tra GET /api/v1/events/{id} dùng đúng locator event_timestamp thống nhất N42-16
    detail_params = {p["name"]: p for p in spec["paths"]["/api/v1/events/{id}"]["get"]["parameters"]}
    assert "event_timestamp" in detail_params and detail_params["event_timestamp"]["required"] is True

    # Kiểm tra ACK required IDs trong OpenAPI schemas
    schemas = spec["components"]["schemas"]
    assert "event_id" in schemas["EventIngestPersistedResponse"]["required"]
    assert "receipt_id" in schemas["EventIngestQueuedResponse"]["required"]
