"""Bộ kiểm thử unit test và benchmark toàn diện cho RFC 3164 Syslog Parser.

Căn cứ: docs/N42-15_DESIGN.md (Bộ ca kiểm thử N15-01 đến N15-24 và mục 8 Benchmark)
"""

import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.models.alert_event import AlertEvent
from app.services.parser import parse_syslog_rfc3164

# Môi trường mặc định theo thiết kế
DEFAULT_IP = "10.10.0.10"
DEFAULT_RECEIVED = datetime(2026, 11, 3, 15, 0, 1, tzinfo=timezone.utc)
DEFAULT_TZ = timezone(timedelta(hours=7))  # UTC+07:00
EXPECTED_TIMESTAMP = datetime(2026, 11, 3, 15, 0, 0, tzinfo=timezone.utc)


def test_n15_01_cisco_link_updown():
    raw = "<189>Nov 03 22:00:00 rtr-01 %LINK-3-UPDOWN: Gi0/1 down"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.parse_error is None
    assert event.facility == 23
    assert event.severity == 5
    assert event.hostname == "rtr-01"
    assert event.vendor == "cisco"
    assert event.program == "LINK"
    assert event.mnemonic == "LINK-3-UPDOWN"
    assert event.message == "Gi0/1 down"
    assert event.event_timestamp == EXPECTED_TIMESTAMP
    assert event.timestamp == EXPECTED_TIMESTAMP  # alias property
    assert event.raw_log == raw  # alias property
    assert isinstance(event.id, UUID)
    assert event.schema_version == "1.0"
    assert event.category == "unknown"


def test_n15_02_cisco_ospf_adjchg():
    raw = "<133>Nov 03 22:00:00 rtr-01 %OSPF-5-ADJCHG: Neighbor down"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.facility == 16
    assert event.severity == 5
    assert event.vendor == "cisco"
    assert event.program == "OSPF"
    assert event.mnemonic == "OSPF-5-ADJCHG"
    assert event.message == "Neighbor down"


def test_n15_03_huawei_power_supply_failed():
    raw = "<131>Nov 03 22:00:00 ne-01 %%01DEVM/2/POWER_SUPPLY_FAILED: Power failed"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.facility == 16
    assert event.severity == 3
    assert event.hostname == "ne-01"
    assert event.vendor == "huawei"
    assert event.program == "DEVM"
    assert event.mnemonic == "POWER_SUPPLY_FAILED"
    assert event.message == "Power failed"


def test_n15_04_huawei_with_suffix_l():
    raw = "<131>Nov 03 22:00:00 ne-01 %%01DEVM/2/POWER_SUPPLY_FAILED(l): Power failed"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.facility == 16
    assert event.severity == 3
    assert event.vendor == "huawei"
    assert event.program == "DEVM"
    assert event.mnemonic == "POWER_SUPPLY_FAILED"
    assert event.message == "Power failed"


def test_n15_05_linux_sshd():
    raw = "<34>Nov  3 22:00:00 host-01 sshd[123]: Login failed"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.facility == 4
    assert event.severity == 2
    assert event.hostname == "host-01"
    assert event.vendor == "linux"
    assert event.program == "sshd"
    assert event.mnemonic is None
    assert event.message == "Login failed"


def test_n15_06_linux_kernel():
    raw = "<0>Nov 03 22:00:00 host-01 kernel: test"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.facility == 0
    assert event.severity == 0
    assert event.vendor == "linux"
    assert event.program == "kernel"
    assert event.message == "test"


def test_n15_07_customapp_unknown_vendor():
    raw = "<191>Nov 03 22:00:00 host-01 customapp[42]: test"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.facility == 23
    assert event.severity == 7
    assert event.vendor == "unknown"
    assert event.program == "customapp"
    assert event.message == "test"


def test_n15_08_plain_content_without_tag():
    raw = "<134>Nov 03 22:00:00 host-01 plain content"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.facility == 16
    assert event.severity == 6
    assert event.vendor == "unknown"
    assert event.program is None
    assert event.mnemonic is None
    assert event.message == "plain content"


@pytest.mark.parametrize(
    "pri_raw",
    [
        "<-1>Nov 03 22:00:00 host-01 test",
        "<192>Nov 03 22:00:00 host-01 test",
        "<abc>Nov 03 22:00:00 host-01 test",
        "<01>Nov 03 22:00:00 host-01 test",
        "<>Nov 03 22:00:00 host-01 test",
    ],
)
def test_n15_09_invalid_pri_variants(pri_raw):
    event = parse_syslog_rfc3164(pri_raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "fallback"
    assert event.parse_error == "invalid_pri"
    assert event.facility == 1
    assert event.severity == 6
    assert event.hostname == DEFAULT_IP
    assert event.vendor == "unknown"
    assert event.message == pri_raw


def test_n15_10_missing_pri():
    raw = "Nov 03 22:00:00 host-01 test"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "fallback"
    assert event.parse_error == "missing_pri"


def test_n15_11_empty_input():
    event = parse_syslog_rfc3164("", DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "fallback"
    assert event.parse_error == "empty_input"


@pytest.mark.parametrize(
    "invalid_time_raw",
    [
        "<34>Nov 31 22:00:00 host-01 test",  # Tháng 11 chỉ có 30 ngày
        "<34>Nov 03 25:00:00 host-01 test",  # Giờ 25 không hợp lệ
    ],
)
def test_n15_12_invalid_timestamp(invalid_time_raw):
    event = parse_syslog_rfc3164(
        invalid_time_raw,
        DEFAULT_IP,
        received_at=DEFAULT_RECEIVED,
        source_timezone=DEFAULT_TZ,
    )
    assert event.parse_status == "fallback"
    assert event.parse_error == "invalid_timestamp"


def test_n15_13_malformed_header_bad_month():
    raw = "<34>Bad 03 22:00:00 host-01 test"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "fallback"
    assert event.parse_error == "malformed_header"


def test_n15_14_year_boundary_wrap_backward():
    raw = "<34>Dec 31 23:59:59 host-01 kernel: test"
    rec = datetime(2027, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=rec, source_timezone=timezone.utc)
    assert event.parse_status == "parsed"
    assert event.event_timestamp == datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    assert event.vendor == "linux"


def test_n15_15_year_boundary_wrap_forward():
    raw = "<34>Jan  1 00:00:01 host-01 kernel: test"
    rec = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=rec, source_timezone=timezone.utc)
    assert event.parse_status == "parsed"
    assert event.event_timestamp == datetime(2027, 1, 1, 0, 0, 1, tzinfo=timezone.utc)


def test_n15_16_leap_year_valid():
    raw = "<34>Feb 29 00:00:00 host-01 kernel: test"
    rec = datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=rec, source_timezone=timezone.utc)
    assert event.parse_status == "parsed"
    assert event.event_timestamp == datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)


def test_n15_17_leap_year_invalid_non_leap():
    raw = "<34>Feb 29 00:00:00 host-01 kernel: test"
    rec = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=rec, source_timezone=timezone.utc)
    assert event.parse_status == "fallback"
    assert event.parse_error == "invalid_timestamp"


def test_n15_18_unicode_and_crlf_suffix():
    raw = "<34>Nov  3 22:00:00 host-01 sshd[123]: Cảnh báo: kết nối lỗi\r\n"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.message == "Cảnh báo: kết nối lỗi"
    assert event.raw_payload == raw  # raw giữ nguyên cả CRLF


@pytest.mark.parametrize(
    "corrupt_raw",
    [
        "<34>Nov 03 22:00:00 host-01 test\x00corrupt",
        "<34>Nov 03 22:00:00 host-01\nline-break inside",
    ],
)
def test_n15_19_control_char_and_internal_newline(corrupt_raw):
    event = parse_syslog_rfc3164(
        corrupt_raw,
        DEFAULT_IP,
        received_at=DEFAULT_RECEIVED,
        source_timezone=DEFAULT_TZ,
    )
    assert event.parse_status == "fallback"
    assert event.parse_error == "malformed_header"


def test_n15_20_unsupported_iso_header():
    raw = "<134>2026-11-03T22:00:00+07:00 host-01 test"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "fallback"
    assert event.parse_error == "unsupported_format"


def test_n15_21_unsupported_fortinet_kv():
    raw = 'date=2026-11-03 time=22:00:00 devname="fg-01" action="deny"'
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "fallback"
    assert event.parse_error == "unsupported_format"


def test_n15_22_payload_length_boundary():
    # Header chuẩn: 35 ký tự
    prefix = "<189>Nov 03 22:00:00 rtr-01 %LINK-3-UPDOWN: "
    rem_len_1024 = 1024 - len(prefix.encode("utf-8"))
    raw_1024 = prefix + ("A" * rem_len_1024)
    raw_1025 = raw_1024 + "B"

    event_1024 = parse_syslog_rfc3164(raw_1024, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event_1024.parse_status == "parsed"

    event_1025 = parse_syslog_rfc3164(raw_1025, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event_1025.parse_status == "fallback"
    assert event_1025.parse_error == "payload_too_large"


def test_n15_23_contract_boundary_exceptions():
    # 1. source_ip không hợp lệ
    with pytest.raises(ValueError, match="Invalid source_ip"):
        parse_syslog_rfc3164("<189>Nov 03 22:00:00 rtr-01 msg", source_ip="not-an-ip")

    # 2. received_at naive
    naive_dt = datetime(2026, 11, 3, 15, 0, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_syslog_rfc3164("<189>Nov 03 22:00:00 rtr-01 msg", received_at=naive_dt)

    # 3. raw không phải chuỗi str
    with pytest.raises(TypeError, match="raw must be str"):
        parse_syslog_rfc3164(b"<189>Nov 03 22:00:00 rtr-01 msg")  # type: ignore


def test_n15_24_empty_message():
    raw = "<34>Nov 03 22:00:00 host-01 kernel: "
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert event.parse_status == "parsed"
    assert event.message == ""
    assert event.program == "kernel"
    assert event.facility == 4
    assert event.severity == 2
    assert event.vendor == "linux"


def test_pydantic_strict_model_validation():
    # Cấm extra field
    with pytest.raises(ValidationError):
        AlertEvent(
            received_at=DEFAULT_RECEIVED,
            event_timestamp=DEFAULT_RECEIVED,
            source_ip="10.10.0.1",
            hostname="host-01",
            facility=1,
            severity=1,
            vendor="cisco",
            extra_field_not_allowed="invalid",
        )

    # Cấm bool cho facility / severity
    with pytest.raises(ValidationError):
        AlertEvent(
            received_at=DEFAULT_RECEIVED,
            event_timestamp=DEFAULT_RECEIVED,
            source_ip="10.10.0.1",
            hostname="host-01",
            facility=True,  # type: ignore
            severity=1,
            vendor="cisco",
        )


def test_throughput_benchmark_dod():
    """Kiểm chứng tiêu chuẩn nghiệm thu DoD: Hiệu năng >= 5.000 log/s trên 1 nhân CPU."""
    samples = [
        "<189>Nov 03 22:00:00 rtr-01 %LINK-3-UPDOWN: Gi0/1 down",
        "<133>Nov 03 22:00:00 rtr-01 %OSPF-5-ADJCHG: Neighbor down",
        "<131>Nov 03 22:00:00 ne-01 %%01DEVM/2/POWER_SUPPLY_FAILED: Power failed",
        "<34>Nov  3 22:00:00 host-01 sshd[123]: Login failed",
        "<191>Nov 03 22:00:00 host-01 customapp[42]: test",
        "Nov 03 22:00:00 host-01 missing pri fallback",
    ]

    # Warm-up 1.000 lượt
    for _ in range(1000):
        for s in samples:
            parse_syslog_rfc3164(s, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)

    # Đo thời gian với 30.000 lượt (5.000 batch x 6 mẫu)
    total_calls = 30000
    start = time.perf_counter()
    for _ in range(5000):
        for s in samples:
            parse_syslog_rfc3164(s, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    elapsed = time.perf_counter() - start
    rate = total_calls / elapsed

    print(f"\n[BENCHMARK] Throughput: {rate:,.2f} logs/s (Thời gian: {elapsed:.3f}s cho {total_calls} bản tin)")
    assert rate >= 5000.0, f"Hiệu năng không đạt DoD (thực tế: {rate:,.2f} logs/s < 5,000 logs/s)"
