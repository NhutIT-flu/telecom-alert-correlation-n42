"""Bộ kiểm thử toàn diện cho Cisco Syslog Parser (N42-23).

Bao phủ:
- Smoke test mẫu mentor Cisco IOS XR (Confluence 7602179)
- TC-PAR-001 (Cisco Catalyst LINK-3-UPDOWN), TC-PAR-002 (LINEPROTO-5-UPDOWN), TC-PAR-003 (Nexus IP-4-DUPADDR)
- Các ca biên: thiếu hostname, thiếu năm/múi giờ, xung đột PRI vs mức hãng, thiếu interface/state (partial)
- Cô lập lỗi sau bản tin hỏng, chống ReDoS, xử lý RawEvent bytes lỗi qua CiscoNormalizer
- Kiểm chứng corpus >= 200 mẫu có nhãn cho mỗi định dạng Cisco được duyệt (AC-02)
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.models.raw_event import RawEvent
from app.services.cisco_parser import CiscoNormalizer, parse_cisco_syslog

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
TZ_PLUS_7 = timezone(timedelta(hours=7))


def _parse_iso_z(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _parse_tz(offset_str: str) -> timezone:
    sign = 1 if offset_str.startswith("+") else -1
    hh, mm = offset_str[1:].split(":")
    return timezone(sign * timedelta(hours=int(hh), minutes=int(mm)))


# ---------------------------------------------------------------------------
# 1. Smoke test mẫu mentor Cisco IOS XR (Confluence 7602179)
# ---------------------------------------------------------------------------


def test_mentor_ios_xr_down_and_up_samples():
    received = datetime(2026, 11, 13, 2, 10, 0, tzinfo=timezone.utc)
    raw_down = (
        "LC/0/1/CPU0:Nov 13 09:06:45.781 +07: ifmgr[193]: "
        "%PKT_INFRA-LINK-3-UPDOWN : Interface TenGigE0/1/0/4, changed state to Down"
    )
    raw_up = (
        "LC/0/1/CPU0:Nov 13 09:06:45.832 +07: ifmgr[193]: "
        "%PKT_INFRA-LINK-3-UPDOWN : Interface TenGigE0/1/0/4, changed state to Up"
    )

    ev_down = parse_cisco_syslog(raw_down, "192.0.2.10", received_at=received, source_timezone=TZ_PLUS_7)
    ev_up = parse_cisco_syslog(raw_up, "192.0.2.10", received_at=received, source_timezone=TZ_PLUS_7)

    assert ev_down.parse_status == "parsed"
    assert ev_down.parse_error is None
    assert ev_down.vendor == "cisco"
    assert ev_down.source_ip == "192.0.2.10"
    # Không nhận nhầm vị trí card LC/0/1/CPU0 làm hostname
    assert ev_down.hostname == "192.0.2.10"
    assert ev_down.card_location == "LC/0/1/CPU0"
    assert ev_down.program == "ifmgr"
    assert ev_down.mnemonic == "PKT_INFRA-LINK-3-UPDOWN"
    assert ev_down.interface == "TenGigE0/1/0/4"
    assert ev_down.state == "DOWN"
    # Mẫu không có PRI -> không tự sinh facility / PRI severity
    assert ev_down.facility is None
    assert ev_down.severity is None
    assert ev_down.vendor_severity == 3
    assert ev_down.normalized_severity == "MAJOR"
    assert ev_down.severity_conflict is False
    assert ev_down.timestamp_inferred is True
    assert ev_down.timestamp_origin == "INFERRED"
    assert ev_down.event_timestamp == datetime(2026, 11, 13, 2, 6, 45, 781000, tzinfo=timezone.utc)
    assert ev_down.received_at == received
    assert ev_down.raw_payload == raw_down

    assert ev_up.parse_status == "parsed"
    assert ev_up.hostname == "192.0.2.10"
    assert ev_up.card_location == "LC/0/1/CPU0"
    assert ev_up.interface == "TenGigE0/1/0/4"
    assert ev_up.state == "UP"
    assert ev_up.event_timestamp == datetime(2026, 11, 13, 2, 6, 45, 832000, tzinfo=timezone.utc)
    assert ev_up.event_timestamp > ev_down.event_timestamp
    assert ev_up.raw_payload == raw_up


# ---------------------------------------------------------------------------
# 2. Ca chuẩn theo TEST_CASE_SPECIFICATION (TC-PAR-001..003)
# ---------------------------------------------------------------------------


def test_tc_par_001_cisco_catalyst_link_down():
    raw = "<133>Nov 06 15:20:00 sw-core-uth %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down"
    received = datetime(2026, 11, 6, 8, 25, 0, tzinfo=timezone.utc)
    ev = parse_cisco_syslog(raw, "192.0.2.20", received_at=received, source_timezone=TZ_PLUS_7)

    assert ev.parse_status == "parsed"
    assert ev.vendor == "cisco"
    assert ev.hostname == "sw-core-uth"
    assert ev.program == "LINK"
    assert ev.mnemonic == "LINK-3-UPDOWN"
    assert ev.interface == "GigabitEthernet0/1"
    assert ev.state == "DOWN"
    assert ev.facility == 16
    assert ev.severity == 5
    assert ev.vendor_severity == 3
    assert ev.severity_conflict is True
    assert ev.normalized_severity == "MAJOR"
    assert ev.event_timestamp == datetime(2026, 11, 6, 8, 20, 0, tzinfo=timezone.utc)


def test_tc_par_002_cisco_lineproto_up():
    raw = (
        "<133>Nov 06 15:20:01 sw-core-uth %LINEPROTO-5-UPDOWN: "
        "Line protocol on Interface GigabitEthernet0/1, changed state to up"
    )
    received = datetime(2026, 11, 6, 8, 25, 0, tzinfo=timezone.utc)
    ev = parse_cisco_syslog(raw, "192.0.2.20", received_at=received, source_timezone=TZ_PLUS_7)

    assert ev.parse_status == "parsed"
    assert ev.vendor == "cisco"
    assert ev.hostname == "sw-core-uth"
    assert ev.program == "LINEPROTO"
    assert ev.mnemonic == "LINEPROTO-5-UPDOWN"
    assert ev.interface == "GigabitEthernet0/1"
    assert ev.state == "UP"
    assert ev.facility == 16
    assert ev.severity == 5
    assert ev.vendor_severity == 5
    assert ev.severity_conflict is False
    assert ev.normalized_severity == "INFO"


def test_tc_par_003_cisco_nexus_ip_dupaddr():
    raw = (
        "<132>Nov 06 15:21:00 nexus-dc-01 %IP-4-DUPADDR: "
        "Duplicate address 10.10.5.100 on Vlan100, sourced by aabb.ccdd.1234"
    )
    received = datetime(2026, 11, 6, 8, 25, 0, tzinfo=timezone.utc)
    ev = parse_cisco_syslog(raw, "192.0.2.30", received_at=received, source_timezone=TZ_PLUS_7)

    assert ev.parse_status == "parsed"
    assert ev.vendor == "cisco"
    assert ev.hostname == "nexus-dc-01"
    assert ev.program == "IP"
    assert ev.mnemonic == "IP-4-DUPADDR"
    assert ev.category == "ip_conflict"
    assert ev.interface == "Vlan100"
    assert ev.duplicate_ip == "10.10.5.100"
    assert ev.mac_address == "aabb.ccdd.1234"
    assert ev.facility == 16
    assert ev.severity == 4
    assert ev.vendor_severity == 4
    assert ev.severity_conflict is False
    assert ev.normalized_severity == "WARNING"


# ---------------------------------------------------------------------------
# 3. Ca biên, xung đột, thiếu trường và cô lập lỗi
# ---------------------------------------------------------------------------


def test_edge_cases_year_boundary_timezone_and_pri_conflict():
    # Giao năm Dec 31 -> nhận vào Jan 01
    raw_dec = (
        "<189>LC/0/1/CPU0:Dec 31 23:59:59.500 +07: ifmgr[193]: "
        "%PKT_INFRA-LINK-3-UPDOWN : Interface TenGigE0/1/0/4, changed state to Down"
    )
    rec = datetime(2027, 1, 1, 0, 0, 5, tzinfo=timezone.utc)
    ev = parse_cisco_syslog(raw_dec, "192.0.2.10", received_at=rec, source_timezone=TZ_PLUS_7)
    assert ev.parse_status == "parsed"
    assert ev.event_timestamp == datetime(2026, 12, 31, 16, 59, 59, 500000, tzinfo=timezone.utc)
    assert ev.facility == 23
    assert ev.severity == 5
    assert ev.vendor_severity == 3
    assert ev.severity_conflict is True
    assert ev.normalized_severity == "MAJOR"

    # IOS XR có năm + có offset -> timestamp_inferred = False
    raw_full_ts = (
        "RP/0/RP0/CPU0:Nov 13 2026 09:06:45.100 +07:00: ifmgr[193]: "
        "%PKT_INFRA-LINK-3-UPDOWN : Interface TenGigE0/1/0/4, changed state to Up"
    )
    ev_full = parse_cisco_syslog(raw_full_ts, "192.0.2.10", received_at=rec, source_timezone=TZ_PLUS_7)
    assert ev_full.timestamp_inferred is False
    assert ev_full.timestamp_origin == "PARSED"
    assert ev_full.event_timestamp == datetime(2026, 11, 13, 2, 6, 45, 100000, tzinfo=timezone.utc)


def test_missing_interface_or_state_returns_partial_without_empty_key():
    raw_no_iface = (
        "LC/0/1/CPU0:Nov 13 09:06:45.781 +07: ifmgr[193]: "
        "%PKT_INFRA-LINK-3-UPDOWN : Interface , changed state to Down"
    )
    ev = parse_cisco_syslog(raw_no_iface, "192.0.2.10", source_timezone=TZ_PLUS_7)
    assert ev.parse_status == "partial"
    assert ev.parse_error == "missing_interface_or_state"
    assert ev.interface is None
    assert ev.state is None
    assert ev.vendor == "cisco"
    assert ev.raw_payload == raw_no_iface

    raw_bad_state = (
        "<133>Nov 06 15:20:00 sw-core-uth %LINK-3-UPDOWN: " "Interface GigabitEthernet0/1, changed state to unknown"
    )
    ev2 = parse_cisco_syslog(raw_bad_state, "192.0.2.20", source_timezone=TZ_PLUS_7)
    assert ev2.parse_status == "partial"
    assert ev2.parse_error == "missing_interface_or_state"
    assert ev2.interface is None
    assert ev2.state is None


def test_malformed_logs_and_error_isolation_before_valid_log():
    received = datetime(2026, 11, 13, 2, 10, 0, tzinfo=timezone.utc)
    bad_inputs = [
        ("", "empty_input"),
        ("<192>Nov 06 15:20:00 sw-01 %LINK-3-UPDOWN: Interface Gi0/1, changed state to down", "invalid_pri"),
        ("<133>Nov 31 15:20:00 sw-01 %LINK-3-UPDOWN: Interface Gi0/1, changed state to down", "invalid_timestamp"),
        ("<133>Nov 06 15:20:00 sw-01\x00bad", "malformed_header"),
        ("Nov 06 15:20:00 host-01 unrecognized log message", "missing_pri"),
        ("date=2026-11-06 time=15:20:00 devname=fg-01 action=deny", "unsupported_format"),
    ]
    valid_xr = (
        "LC/0/1/CPU0:Nov 13 09:06:45.781 +07: ifmgr[193]: "
        "%PKT_INFRA-LINK-3-UPDOWN : Interface TenGigE0/1/0/4, changed state to Down"
    )

    for bad_raw, expected_err in bad_inputs:
        bad_ev = parse_cisco_syslog(bad_raw, "192.0.2.10", received_at=received, source_timezone=TZ_PLUS_7)
        assert bad_ev.parse_status == "fallback"
        assert bad_ev.parse_error == expected_err
        assert bad_ev.raw_payload == bad_raw

        # Bản tin hợp lệ ngay sau mẫu lỗi phải xử lý sạch, không bị rò trạng thái lỗi
        good_ev = parse_cisco_syslog(valid_xr, "192.0.2.10", received_at=received, source_timezone=TZ_PLUS_7)
        assert good_ev.parse_status == "parsed"
        assert good_ev.parse_error is None
        assert good_ev.interface == "TenGigE0/1/0/4"
        assert good_ev.state == "DOWN"


def test_normalizer_raw_event_and_invalid_utf8_bytes():
    normalizer = CiscoNormalizer(source_timezone=TZ_PLUS_7)
    received = datetime(2026, 11, 13, 2, 10, 0, tzinfo=timezone.utc)

    valid_raw = RawEvent(
        payload=(
            b"LC/0/1/CPU0:Nov 13 09:06:45.781 +07: ifmgr[193]: "
            b"%PKT_INFRA-LINK-3-UPDOWN : Interface TenGigE0/1/0/4, changed state to Down"
        ),
        source_ip="192.0.2.10",
        received_at=received,
        channel="udp",
    )
    assert normalizer.can_parse(valid_raw) is True
    ev = normalizer.parse(valid_raw)
    assert ev.parse_status == "parsed"
    assert ev.interface == "TenGigE0/1/0/4"

    bad_bytes = RawEvent(
        payload=b"\xff\xfe\xfd invalid utf8 bytes",
        source_ip="192.0.2.10",
        received_at=received,
        channel="udp",
    )
    assert normalizer.can_parse(bad_bytes) is False
    ev_bad = normalizer.parse(bad_bytes)
    assert ev_bad.parse_status == "fallback"
    assert ev_bad.parse_error == "invalid_encoding"


def test_redos_resistance_long_adversarial_line():
    # Payload dài gần trần, không tạo catastrophic backtracking
    adversarial = "LC/0/1/CPU0:Nov 13 09:06:45.781 +07: ifmgr[193]: " + ("A" * 1800)
    start = time.perf_counter()
    ev = parse_cisco_syslog(adversarial, "192.0.2.10", source_timezone=TZ_PLUS_7)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    assert ev.parse_status == "fallback"
    assert elapsed_ms < 100.0, f"Thời gian xử lý bất thường: {elapsed_ms:.2f}ms"


# ---------------------------------------------------------------------------
# 4. Kiểm chứng Corpus >= 200 mẫu/định dạng theo AC-02 & SHA-256 manifest
# ---------------------------------------------------------------------------


def test_cisco_corpus_manifest_and_sha256():
    manifest_path = FIXTURES_DIR / "cisco_corpus_manifest.json"
    assert manifest_path.exists(), "Thiếu manifest corpus Cisco"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["minimum_per_format_ac02"] >= 200
    assert len(manifest["datasets"]) == 3

    for ds in manifest["datasets"]:
        fpath = FIXTURES_DIR / ds["file"]
        assert fpath.exists()
        # Chuẩn hóa CRLF -> LF khi tính SHA-256 để khớp giữa Windows (autocrlf) và Linux CI
        canonical_bytes = fpath.read_bytes().replace(b"\r\n", b"\n")
        actual_sha = hashlib.sha256(canonical_bytes).hexdigest()
        assert actual_sha == ds["sha256"], f"Sai lệch SHA-256 cho {ds['file']}"
        assert ds["count"] >= 200, f"Corpus {ds['file']} chưa đạt 200 mẫu"


@pytest.mark.parametrize(
    "fixture_file",
    [
        "cisco_ios_xr.jsonl",
        "cisco_ios.jsonl",
        "cisco_nexus.jsonl",
    ],
)
def test_cisco_labeled_corpus_all_fields_match(fixture_file: str):
    fpath = FIXTURES_DIR / fixture_file
    lines = [line for line in fpath.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 200

    for line in lines:
        item = json.loads(line)
        exp = item["expected"]
        ev = parse_cisco_syslog(
            item["raw"],
            item["source_ip"],
            received_at=_parse_iso_z(item["received_at"]),
            source_timezone=_parse_tz(item["source_timezone"]),
        )

        assert ev.parse_status == exp["parse_status"], item["case_id"]
        assert ev.parse_error == exp["parse_error"], item["case_id"]
        assert ev.vendor == exp["vendor"], item["case_id"]
        assert ev.hostname == exp["hostname"], item["case_id"]
        assert ev.card_location == exp["card_location"], item["case_id"]
        assert ev.program == exp["program"], item["case_id"]
        assert ev.mnemonic == exp["mnemonic"], item["case_id"]
        assert ev.interface == exp["interface"], item["case_id"]
        assert ev.state == exp["state"], item["case_id"]
        assert ev.facility == exp["facility"], item["case_id"]
        assert ev.severity == exp["severity"], item["case_id"]
        assert ev.vendor_severity == exp["vendor_severity"], item["case_id"]
        assert ev.normalized_severity == exp["normalized_severity"], item["case_id"]
        assert ev.severity_conflict == exp["severity_conflict"], item["case_id"]
        assert ev.timestamp_inferred == exp["timestamp_inferred"], item["case_id"]
        assert ev.event_timestamp == _parse_iso_z(exp["event_timestamp"]), item["case_id"]
        assert ev.category == exp["category"], item["case_id"]
        assert ev.raw_payload == item["raw"], item["case_id"]
        if "duplicate_ip" in exp:
            assert ev.duplicate_ip == exp["duplicate_ip"], item["case_id"]
        if "mac_address" in exp:
            assert ev.mac_address == exp["mac_address"], item["case_id"]
