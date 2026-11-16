"""Bộ kiểm thử xác thực Hợp đồng API và DTO Sự kiện v1.0 (N42-62).

Căn cứ:
  - docs/N42-62_DESIGN.md
  - app/schemas/event_contract.py
  - tests/fixtures/contract_v1/
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.alert_event import AlertEvent
from app.schemas.event_contract import (
    EventIngestBatchRequest,
    EventIngestRequest,
    EventIngestResponse,
    EventListResponse,
    EventView,
    decode_cursor,
    encode_cursor,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "contract_v1"


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
    # 1. raw_message rỗng
    with pytest.raises(ValidationError):
        EventIngestRequest(raw_message="")

    # 2. source_ip không phải địa chỉ IP hợp lệ
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
    # 1. Durable response
    durable_data = json.loads((FIXTURES_DIR / "ingest_response_durable.json").read_text(encoding="utf-8"))
    durable_resp = EventIngestResponse.model_validate(durable_data)
    assert durable_resp.status == "persisted"
    assert durable_resp.event_id is not None
    assert durable_resp.receipt_id is None

    # 2. Queued response
    queued_data = json.loads((FIXTURES_DIR / "ingest_response_queued.json").read_text(encoding="utf-8"))
    queued_resp = EventIngestResponse.model_validate(queued_data)
    assert queued_resp.status == "queued"
    assert queued_resp.receipt_id is not None
    assert queued_resp.event_id is None


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

    # Mã hóa cursor
    cursor_str = encode_cursor(original_ts, original_id)
    assert isinstance(cursor_str, str)
    assert len(cursor_str) > 0

    # Giải mã cursor
    decoded_ts, decoded_id = decode_cursor(cursor_str)
    assert decoded_id == original_id
    assert decoded_ts == original_ts


def test_cursor_decode_invalid() -> None:
    """Xác thực giải mã cursor hỏng ném ngoại lệ ValueError an toàn."""
    with pytest.raises(ValueError, match="Invalid pagination cursor"):
        decode_cursor("not-a-valid-base64-string!!!")

    with pytest.raises(ValueError, match="Invalid pagination cursor"):
        # Base64 hợp lệ nhưng không phải JSON
        decode_cursor("SGVsbG8gV29ybGQ=")

