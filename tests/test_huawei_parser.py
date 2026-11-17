"""Bộ kiểm thử đơn vị cho Module Parser chuẩn hóa cảnh báo Huawei (N42-24 - Ngày 1).

Căn cứ:
- Jira: N42-24 (BE2 - Phạm Tấn Thành)
- docs/TEST_CASE_SPECIFICATION.md (Mục 6.4: TC-PAR-004, TC-PAR-005)
- docs/scenarios/KB-02-power-failure.md & docs/scenarios/KB-06-cpu-high-temp.md
- Tiêu chí nghiệm thu AC-02, FR-04, NFR-01
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from app.services.parser import parse_syslog_rfc3164

# Môi trường kiểm thử chuẩn hóa
DEFAULT_IP = "10.10.0.10"
DEFAULT_RECEIVED = datetime(2026, 11, 17, 10, 0, 1, tzinfo=timezone.utc)
DEFAULT_TZ = timezone(timedelta(hours=7))  # UTC+07:00


def test_tc_par_004_huawei_ne40e_power_supply_failed() -> None:
    """TC-PAR-004: Bóc tách mẫu Huawei NE40E POWER_SUPPLY_FAILED (P1 - CRITICAL).

    Kỳ vọng:
    - vendor = "huawei"
    - hostname = "ne40e-bras-01"
    - program = "DEVM"
    - mnemonic = "POWER_SUPPLY_FAILED"
    - message = "Power supply module 2 failed"
    - facility = 16, severity = 3
    - parse_status = "parsed"
    """
    raw = "<131>Nov 06 15:22:00 ne40e-bras-01 %%01DEVM/2/POWER_SUPPLY_FAILED: Power supply module 2 failed"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)

    assert event.parse_status == "parsed"
    assert event.parse_error is None
    assert event.vendor == "huawei"
    assert event.hostname == "ne40e-bras-01"
    assert event.facility == 16
    assert event.severity == 3
    assert event.program == "DEVM"
    assert event.mnemonic == "POWER_SUPPLY_FAILED"
    assert event.message == "Power supply module 2 failed"
    assert event.raw_payload == raw


def test_tc_par_005_huawei_s5700_cpu_temp_alarm() -> None:
    """TC-PAR-005: Bóc tách mẫu Huawei S5700 CPU_TEMP_ALARM (P2 - HIGH).

    Kỳ vọng:
    - vendor = "huawei"
    - hostname = "s5700-01"
    - program = "DEVM"
    - mnemonic = "CPU_TEMP_ALARM"
    - message = "CPU temperature reached 85 C, threshold 80 C"
    - parse_status = "parsed"
    """
    raw = "<131>Nov 06 15:23:00 s5700-01 %%01DEVM/2/CPU_TEMP_ALARM: CPU temperature reached 85 C, threshold 80 C"
    event = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)

    assert event.parse_status == "parsed"
    assert event.parse_error is None
    assert event.vendor == "huawei"
    assert event.hostname == "s5700-01"
    assert event.program == "DEVM"
    assert event.mnemonic == "CPU_TEMP_ALARM"
    assert event.message == "CPU temperature reached 85 C, threshold 80 C"


def test_huawei_vrp_flag_variants() -> None:
    """Kiểm tra các biến thể cờ VRP của Huawei: (l) log, (s) trap, (m) security, (d) debug."""
    # 1. Cờ (l) - Local logging
    raw_l = "<131>Nov 17 10:00:00 hw-ne40e %%01DEVM/2/POWER_SUPPLY_FAILED(l): Power module 1 down"
    ev_l = parse_syslog_rfc3164(raw_l, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert ev_l.vendor == "huawei"
    assert ev_l.mnemonic == "POWER_SUPPLY_FAILED"
    assert ev_l.message == "Power module 1 down"

    # 2. Cờ (s) - SNMP trap notification
    raw_s = "<131>Nov 17 10:00:00 hw-ne40e %%01DEVM/2/POWER_SUPPLY_FAILED(s): Power module 2 down"
    ev_s = parse_syslog_rfc3164(raw_s, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert ev_s.vendor == "huawei"
    assert ev_s.mnemonic == "POWER_SUPPLY_FAILED"
    assert ev_s.message == "Power module 2 down"

    # 3. Cờ kèm sequence index [0]
    raw_seq = (
        "<132>Nov 17 10:00:00 hw-s5700 %%01IFNET/4/IF_STATE(l)[0]: "
        "Interface GigabitEthernet0/0/1 has turned into DOWN state."
    )
    ev_seq = parse_syslog_rfc3164(raw_seq, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert ev_seq.vendor == "huawei"
    assert ev_seq.program == "IFNET"
    assert ev_seq.mnemonic == "IF_STATE"
    assert ev_seq.message == "Interface GigabitEthernet0/0/1 has turned into DOWN state."


def test_huawei_network_protocol_modules() -> None:
    """Kiểm tra các module định tuyến và phần cứng phổ biến của Huawei (BGP, OSPF, FAN, ENTITY)."""
    cases = [
        (
            "<130>Nov 17 10:15:00 rtr-pe-01 %%01BGP/2/BACKWARD: The BGP FSM moves from Established to Idle",
            "BGP",
            "BACKWARD",
            "The BGP FSM moves from Established to Idle",
        ),
        (
            "<130>Nov 17 10:20:00 rtr-pe-01 %%01OSPF/2/NBR_CHANGE: Neighbor 10.10.1.2 changes state to Down",
            "OSPF",
            "NBR_CHANGE",
            "Neighbor 10.10.1.2 changes state to Down",
        ),
        (
            "<131>Nov 17 10:25:00 sw-dist-01 %%01FAN/2/FAN_FAIL: Fan tray 1 failed",
            "FAN",
            "FAN_FAIL",
            "Fan tray 1 failed",
        ),
        (
            "<131>Nov 17 10:30:00 ne40e-02 %%10ENTITY/2/ENTITY_REMOVE: The physical entity was removed",
            "ENTITY",
            "ENTITY_REMOVE",
            "The physical entity was removed",
        ),
    ]

    for raw, exp_prog, exp_mnem, exp_msg in cases:
        ev = parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
        assert ev.parse_status == "parsed"
        assert ev.vendor == "huawei"
        assert ev.program == exp_prog
        assert ev.mnemonic == exp_mnem
        assert ev.message == exp_msg


def test_huawei_prefix_and_formatting_variants() -> None:
    """Kiểm tra độ linh hoạt với các prefix %%01, %%10, %%, % của Huawei."""
    # Prefix %% không có số version
    raw_double = "<131>Nov 17 10:35:00 hw-01 %%DEVM/2/POWER_SUPPLY_FAILED: Power supply failed"
    ev_double = parse_syslog_rfc3164(raw_double, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert ev_double.vendor == "huawei"
    assert ev_double.program == "DEVM"
    assert ev_double.mnemonic == "POWER_SUPPLY_FAILED"

    # Prefix % (1 dấu %) nhưng có dấu / phân cách kiểu Huawei (khác với dấu - của Cisco)
    raw_single = "<131>Nov 17 10:35:00 hw-01 %DEVM/2/POWER_SUPPLY_FAILED: Power supply failed"
    ev_single = parse_syslog_rfc3164(raw_single, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    assert ev_single.vendor == "huawei"
    assert ev_single.program == "DEVM"
    assert ev_single.mnemonic == "POWER_SUPPLY_FAILED"


def test_huawei_throughput_performance() -> None:
    """NFR-01: Đo thông lượng bóc tách cảnh báo Huawei đạt >= 1,000 msg/s."""
    raw = "<131>Nov 06 15:22:00 ne40e-bras-01 %%01DEVM/2/POWER_SUPPLY_FAILED: Power supply module 2 failed"
    iterations = 2000

    start_time = time.perf_counter()
    for _ in range(iterations):
        parse_syslog_rfc3164(raw, DEFAULT_IP, received_at=DEFAULT_RECEIVED, source_timezone=DEFAULT_TZ)
    elapsed = time.perf_counter() - start_time

    rate = iterations / elapsed
    assert rate >= 1000.0, f"Thông lượng parser Huawei không đạt: {rate:.1f} msg/s (kỳ vọng >= 1000 msg/s)"

