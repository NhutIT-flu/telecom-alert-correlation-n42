"""Module Cisco Parser: Giải mã và chuẩn hóa cảnh báo Syslog Cisco IOS XR, IOS và Nexus.

Căn cứ:
- Jira N42-23 & Confluence 7602179 (mẫu mentor Cisco IOS XR & IOS/Nexus)
- docs/N42-23_DESIGN.md
- docs/TEST_CASE_SPECIFICATION.md (TC-PAR-001..003)
- n42-ai-kit/docs/INTERFACES.md
"""

from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Optional

from app.models.alert_event import AlertEvent, NormalizedSeverityType, PortStateType, TimestampOriginType
from app.models.raw_event import RawEvent

# Phiên bản bảng ánh xạ mức độ nghiêm trọng (đồng bộ N42-26)
CISCO_SEVERITY_MAP_VERSION = "0.9-n42-23"

# Giới hạn dung lượng tối đa cho một bản tin Cisco Syslog (UTF-8 bytes)
MAX_CISCO_PAYLOAD_BYTES = 2048

MONTH_MAP = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

# Bảng ánh xạ chuẩn 0..7 -> mức nghiệp vụ (đồng bộ D-01 & kiến trúc 5 mức + UNKNOWN)
SEVERITY_NUMBER_TO_NORMALIZED: dict[int, NormalizedSeverityType] = {
    0: "CRITICAL",
    1: "CRITICAL",
    2: "CRITICAL",
    3: "MAJOR",
    4: "WARNING",
    5: "INFO",
    6: "INFO",
    7: "DEBUG",
}

# Regex kiểm tra PRI hợp lệ (0 hoặc 1-191, không leading zero)
RE_PRI_PREFIX = re.compile(r"^<(?P<pri_str>[^>]*)>(?P<rest>.*)$", re.DOTALL)
RE_VALID_PRI = re.compile(r"^(?:0|[1-9]\d{0,2})$")

# Regex nhận diện định dạng ngoài phạm vi Cisco (ví dụ Fortinet KV)
RE_FORTINET_KV = re.compile(r"^date=\d{4}-\d{2}-\d{2}\s+time=\d{2}:\d{2}:\d{2}\b")

# Regex Cisco IOS XR header: [hostname] <LC|RP|SP|RSP|DRP>/r/s/CPUx:<timestamp> <rest>
RE_IOS_XR_CARD = re.compile(
    r"^(?:(?P<host>[A-Za-z0-9_.-]+)\s+)?"
    r"(?P<card>(?:LC|RP|SP|RSP|DRP)/\d+/[A-Za-z0-9]+/CPU\d+):"
    r"(?P<after_card>.*)$",
    re.DOTALL,
)

# Regex Cisco IOS XR process tag trước phần thân %FACILITY-N-MNEMONIC
RE_IOS_XR_PROC = re.compile(
    r"^(?:(?P<host>[A-Za-z0-9_.-]+)\s+)?" r"(?P<proc>[A-Za-z0-9_.-]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<body>%.*)$",
    re.DOTALL,
)

# Regex thời gian dạng Syslog (hỗ trợ thiếu năm, có năm, mili giây, offset +07 / +07:00 / UTC / Z)
RE_SYSLOG_TS = re.compile(
    r"^(?P<month>[A-Za-z]{3})\s+(?P<day>\d{1,2})\s+"
    r"(?:(?P<year>\d{4})\s+)?"
    r"(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})"
    r"(?:\.(?P<frac>\d{1,6}))?"
    r"(?:\s+(?P<tz>[+-]\d{2}(?::?\d{2})?|UTC|GMT|Z))?"
    r"(?:\s*:)?\s*(?P<rest>.*)$",
    re.DOTALL,
)

# Regex thời gian ISO-8601 (dùng trong FIXTURE-01/05 Cisco IOS/Nexus)
RE_ISO_TS = re.compile(
    r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T"
    r"(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})"
    r"(?:\.(?P<frac>\d{1,6}))?"
    r"(?P<tz>Z|[+-]\d{2}(?::?\d{2})?)?"
    r"\s+(?P<rest>.*)$",
    re.DOTALL,
)

# Regex tách hostname (tùy chọn) + thông báo %FACILITY-N-MNEMONIC cho Cisco IOS/Nexus
RE_IOS_HOST_AND_MSG = re.compile(
    r"^(?:(?P<host>[A-Za-z0-9_.-]+)\s+)?(?P<body>%.*)$",
    re.DOTALL,
)

# Regex thông báo chuẩn Cisco: %FACILITY-N-MNEMONIC : message
RE_CISCO_BODY = re.compile(
    r"^%(?P<mnemonic>(?P<fac>[A-Za-z0-9_-]+)-(?P<vsev>[0-7])-(?P<code>[A-Za-z0-9_-]+))\s*:\s?(?P<msg>.*)$",
    re.DOTALL,
)

# Regex bóc cổng & trạng thái chuẩn IOS / IOS XR (LINK-3-UPDOWN, LINEPROTO-5-UPDOWN, PKT_INFRA-LINK-3-UPDOWN)
RE_PORT_CHANGED_STATE = re.compile(
    r"^(?:Line protocol on )?Interface\s+(?P<iface>[A-Za-z][A-Za-z0-9./_-]*)\s*,\s*"
    r"changed state to\s+(?P<state>administratively down|down|up)\b",
    re.IGNORECASE,
)

# Regex bóc cổng & trạng thái Nexus NX-OS (%ETHPORT-5-IF_UP / %ETHPORT-5-IF_DOWN_*)
RE_NEXUS_ETHPORT = re.compile(
    r"^Interface\s+(?P<iface>[A-Za-z][A-Za-z0-9./_-]*)\s+is\s+(?P<state>down|up)\b",
    re.IGNORECASE,
)

# Regex bóc cổng & trạng thái dạng rút gọn (ví dụ: Gi0/1 down)
RE_PORT_SHORT = re.compile(
    r"^(?P<iface>(?:GigabitEthernet|TenGigabitEthernet|TenGigE|FastEthernet|Ethernet|"
    r"HundredGigE|FortyGigE|Port-channel|Bundle-Ether|MgmtEth|Loopback|Vlan|"
    r"Gi|Te|Fa|Eth|Po|BE|Lo|Hu|Fo)[A-Za-z0-9./_-]*)\s+(?P<state>down|up)\b",
    re.IGNORECASE,
)

# Regex bóc cảnh báo xung đột IP Cisco Nexus (%IP-4-DUPADDR)
RE_IP_DUPADDR = re.compile(
    r"^Duplicate address\s+(?P<dup_ip>\S+)\s+on\s+(?P<iface>[A-Za-z][A-Za-z0-9./_-]*)\s*,\s*"
    r"sourced by\s+(?P<mac>[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}|(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})\b",
    re.IGNORECASE,
)


def map_cisco_severity(
    pri_severity: Optional[int],
    vendor_severity: Optional[int],
) -> tuple[NormalizedSeverityType, bool]:
    """Ánh xạ mức độ nghiêm trọng từ PRI và mã hãng sang thang chuẩn N42-26.

    Ưu tiên vendor_severity khi cả hai cùng tồn tại, đồng thời gắn cờ conflict nếu lệch nhau.
    """
    conflict = pri_severity is not None and vendor_severity is not None and pri_severity != vendor_severity
    effective = vendor_severity if vendor_severity is not None else pri_severity
    if effective is None:
        return "UNKNOWN", conflict
    return SEVERITY_NUMBER_TO_NORMALIZED.get(effective, "UNKNOWN"), conflict


def _parse_tz_token(tz_str: str) -> Optional[timezone]:
    """Chuyển chuỗi múi giờ (+07, +0700, +07:00, -05:00, UTC, GMT, Z) thành timezone cố định."""
    if tz_str in ("Z", "UTC", "GMT"):
        return timezone.utc
    m = re.fullmatch(r"([+-])(\d{2})(?::?(\d{2}))?", tz_str)
    if not m:
        return None
    sign = 1 if m.group(1) == "+" else -1
    hours = int(m.group(2))
    minutes = int(m.group(3) or "0")
    if hours > 23 or minutes > 59:
        return None
    return timezone(sign * timedelta(hours=hours, minutes=minutes))


def _frac_to_microseconds(frac: Optional[str]) -> int:
    if not frac:
        return 0
    return int(frac.ljust(6, "0"))


def _infer_year_timestamp(
    month_num: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    microsecond: int,
    tz: tzinfo,
    received_at: datetime,
) -> Optional[datetime]:
    """Suy diễn năm gần received_at nhất trong múi giờ nguồn và quy về UTC."""
    rec_in_tz = received_at.astimezone(tz)
    candidates: list[tuple[timedelta, datetime]] = []
    for y in (rec_in_tz.year - 1, rec_in_tz.year, rec_in_tz.year + 1):
        try:
            cand_dt = datetime(y, month_num, day, hour, minute, second, microsecond, tzinfo=tz)
            cand_utc = cand_dt.astimezone(timezone.utc)
            candidates.append((abs(cand_utc - received_at), cand_utc))
        except ValueError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][1]


def _parse_cisco_timestamp(
    ts_text: str,
    received_at: datetime,
    source_timezone: tzinfo,
) -> Optional[tuple[datetime, bool, TimestampOriginType, str]]:
    """Phân tích timestamp Syslog hoặc ISO-8601; trả (utc_dt, inferred, origin, remaining_text)."""
    iso_match = RE_ISO_TS.match(ts_text)
    if iso_match:
        year = int(iso_match.group("year"))
        month = int(iso_match.group("month"))
        day = int(iso_match.group("day"))
        hour = int(iso_match.group("hour"))
        minute = int(iso_match.group("min"))
        second = int(iso_match.group("sec"))
        microsecond = _frac_to_microseconds(iso_match.group("frac"))
        tz_str = iso_match.group("tz")
        if tz_str is not None:
            parsed_tz = _parse_tz_token(tz_str)
            if parsed_tz is None:
                return None
            tz: tzinfo = parsed_tz
            inferred = False
            origin: TimestampOriginType = "PARSED"
        else:
            tz = source_timezone
            inferred = True
            origin = "INFERRED"
        try:
            dt = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tz)
        except ValueError:
            return None
        return dt.astimezone(timezone.utc), inferred, origin, iso_match.group("rest")

    sys_match = RE_SYSLOG_TS.match(ts_text)
    if not sys_match:
        return None

    month_num = MONTH_MAP.get(sys_match.group("month"))
    if month_num is None:
        return None

    day = int(sys_match.group("day"))
    hour = int(sys_match.group("hour"))
    minute = int(sys_match.group("min"))
    second = int(sys_match.group("sec"))
    if hour > 23 or minute > 59 or second > 59:
        return None

    microsecond = _frac_to_microseconds(sys_match.group("frac"))
    year_str = sys_match.group("year")
    tz_str = sys_match.group("tz")

    if tz_str is not None:
        parsed_tz = _parse_tz_token(tz_str)
        if parsed_tz is None:
            return None
        tz = parsed_tz
        tz_missing = False
    else:
        tz = source_timezone
        tz_missing = True

    if year_str is not None:
        try:
            dt = datetime(int(year_str), month_num, day, hour, minute, second, microsecond, tzinfo=tz)
        except ValueError:
            return None
        utc_dt = dt.astimezone(timezone.utc)
        inferred = tz_missing
        origin = "INFERRED" if inferred else "PARSED"
        return utc_dt, inferred, origin, sys_match.group("rest")

    utc_dt_inferred = _infer_year_timestamp(month_num, day, hour, minute, second, microsecond, tz, received_at)
    if utc_dt_inferred is None:
        return None
    return utc_dt_inferred, True, "INFERRED", sys_match.group("rest")


def _make_cisco_fallback(
    raw: str,
    source_ip: str,
    received_at: datetime,
    parse_error: str,
    *,
    facility: Optional[int] = 1,
    severity: Optional[int] = 6,
) -> AlertEvent:
    """Tạo bản ghi chẩn đoán fallback an toàn, giữ nguyên raw_payload."""
    return AlertEvent(
        received_at=received_at,
        event_timestamp=received_at,
        timestamp_inferred=True,
        timestamp_origin="RECEIVED_FALLBACK",
        source_ip=source_ip,
        hostname=source_ip,
        card_location=None,
        facility=facility,
        severity=severity,
        vendor_severity=None,
        normalized_severity="UNKNOWN",
        severity_conflict=False,
        vendor="unknown",
        program=None,
        mnemonic=None,
        category="unknown",
        interface=None,
        state=None,
        duplicate_ip=None,
        mac_address=None,
        message=raw,
        raw_payload=raw,
        parse_status="fallback",
        parse_error=parse_error,
    )


def _normalize_port_state(raw_state: str) -> PortStateType:
    lowered = raw_state.strip().lower()
    if lowered == "up":
        return "UP"
    return "DOWN"


def _extract_cisco_details(
    fac: str,
    code: str,
    msg: str,
) -> tuple[str, Optional[str], Optional[PortStateType], Optional[str], Optional[str], str, Optional[str]]:
    """Trích xuất thông tin nghiệp vụ (category, interface, state, dup_ip, mac, parse_status, parse_error)."""
    # 1. Nhóm cảnh báo trạng thái cổng
    is_port_event = code == "UPDOWN" or code == "IF_UP" or code.startswith("IF_DOWN")
    if is_port_event:
        m = RE_PORT_CHANGED_STATE.match(msg) or RE_NEXUS_ETHPORT.match(msg) or RE_PORT_SHORT.match(msg)
        if m:
            iface = m.group("iface").strip()
            state = _normalize_port_state(m.group("state"))
            if iface:
                return "link_status", iface, state, None, None, "parsed", None
        return "link_status", None, None, None, None, "partial", "missing_interface_or_state"

    # 2. Nhóm cảnh báo xung đột IP (%IP-4-DUPADDR)
    if fac == "IP" and code == "DUPADDR":
        m_dup = RE_IP_DUPADDR.match(msg)
        if m_dup:
            dup_ip_str = m_dup.group("dup_ip").strip()
            iface = m_dup.group("iface").strip()
            mac = m_dup.group("mac").strip().lower()
            try:
                dup_ip_norm = str(ipaddress.ip_address(dup_ip_str))
            except ValueError:
                return "ip_conflict", None, None, None, None, "partial", "missing_conflict_fields"
            if iface:
                return "ip_conflict", iface, None, dup_ip_norm, mac, "parsed", None
        return "ip_conflict", None, None, None, None, "partial", "missing_conflict_fields"

    # 3. Các sự kiện Cisco hợp lệ khác (ví dụ OSPF, BGP)
    if fac in ("OSPF", "BGP") or "BGP" in fac or "OSPF" in fac:
        return "routing", None, None, None, None, "parsed", None
    return "unknown", None, None, None, None, "parsed", None


def _build_cisco_event(
    *,
    raw: str,
    source_ip: str,
    received_at: datetime,
    event_timestamp: datetime,
    timestamp_inferred: bool,
    timestamp_origin: TimestampOriginType,
    hostname: str,
    card_location: Optional[str],
    facility: Optional[int],
    pri_severity: Optional[int],
    program: str,
    mnemonic: str,
    vendor_severity: int,
    fac: str,
    code: str,
    msg: str,
) -> AlertEvent:
    normalized_sev, conflict = map_cisco_severity(pri_severity, vendor_severity)
    category, interface, state, dup_ip, mac, parse_status, parse_error = _extract_cisco_details(fac, code, msg)
    return AlertEvent(
        received_at=received_at,
        event_timestamp=event_timestamp,
        timestamp_inferred=timestamp_inferred,
        timestamp_origin=timestamp_origin,
        source_ip=source_ip,
        hostname=hostname,
        card_location=card_location,
        facility=facility,
        severity=pri_severity,
        vendor_severity=vendor_severity,
        normalized_severity=normalized_sev,
        severity_conflict=conflict,
        vendor="cisco",
        program=program,
        mnemonic=mnemonic,
        category=category,
        interface=interface,
        state=state,
        duplicate_ip=dup_ip,
        mac_address=mac,
        message=msg,
        raw_payload=raw,
        parse_status=parse_status,  # type: ignore[arg-type]
        parse_error=parse_error,
    )


def _parse_ios_xr(
    *,
    raw: str,
    after_pri: str,
    source_ip: str,
    received_at: datetime,
    source_timezone: tzinfo,
    facility: Optional[int],
    pri_severity: Optional[int],
) -> Optional[AlertEvent]:
    """Phân tích nhánh Cisco IOS XR (ưu tiên mẫu có card location như LC/0/1/CPU0)."""
    xr_match = RE_IOS_XR_CARD.match(after_pri)
    if not xr_match:
        return None

    host_before_card = xr_match.group("host")
    card_location = xr_match.group("card")
    after_card = xr_match.group("after_card").lstrip()

    ts_res = _parse_cisco_timestamp(after_card, received_at, source_timezone)
    if ts_res is None:
        return _make_cisco_fallback(
            raw, source_ip, received_at, "invalid_timestamp", facility=facility, severity=pri_severity
        )

    event_timestamp, timestamp_inferred, timestamp_origin, after_ts = ts_res

    proc_match = RE_IOS_XR_PROC.match(after_ts)
    if proc_match:
        host_after_ts = proc_match.group("host")
        program = proc_match.group("proc")
        body = proc_match.group("body")
    else:
        host_and_msg = RE_IOS_HOST_AND_MSG.match(after_ts)
        if not host_and_msg:
            return _make_cisco_fallback(
                raw, source_ip, received_at, "malformed_header", facility=facility, severity=pri_severity
            )
        host_after_ts = host_and_msg.group("host")
        program = ""
        body = host_and_msg.group("body")

    body_match = RE_CISCO_BODY.match(body)
    if not body_match:
        return _make_cisco_fallback(
            raw, source_ip, received_at, "unsupported_format", facility=facility, severity=pri_severity
        )

    fac = body_match.group("fac")
    vsev = int(body_match.group("vsev"))
    code = body_match.group("code")
    mnemonic = body_match.group("mnemonic")
    msg = body_match.group("msg")

    # Tuyệt đối không dùng card_location làm hostname; fallback về source_ip nếu thiếu hostname
    hostname = host_before_card or host_after_ts or source_ip
    effective_program = program or fac

    return _build_cisco_event(
        raw=raw,
        source_ip=source_ip,
        received_at=received_at,
        event_timestamp=event_timestamp,
        timestamp_inferred=timestamp_inferred,
        timestamp_origin=timestamp_origin,
        hostname=hostname,
        card_location=card_location,
        facility=facility,
        pri_severity=pri_severity,
        program=effective_program,
        mnemonic=mnemonic,
        vendor_severity=vsev,
        fac=fac,
        code=code,
        msg=msg,
    )


def _parse_ios_nexus(
    *,
    raw: str,
    after_pri: str,
    has_pri: bool,
    source_ip: str,
    received_at: datetime,
    source_timezone: tzinfo,
    facility: Optional[int],
    pri_severity: Optional[int],
) -> AlertEvent:
    """Phân tích nhánh Cisco IOS và Cisco Nexus."""
    ts_res = _parse_cisco_timestamp(after_pri, received_at, source_timezone)
    if ts_res is None:
        if not has_pri:
            return _make_cisco_fallback(raw, source_ip, received_at, "missing_pri")
        # Phân biệt tháng sai (malformed_header) với ngày/giờ không tồn tại (invalid_timestamp)
        if re.match(
            r"^(?:[A-Za-z]{3}\s+\d{1,2}\s+(?:\d{4}\s+)?\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            after_pri,
        ):
            return _make_cisco_fallback(raw, source_ip, received_at, "invalid_timestamp")
        return _make_cisco_fallback(raw, source_ip, received_at, "malformed_header")

    event_timestamp, timestamp_inferred, timestamp_origin, after_ts = ts_res

    host_and_msg = RE_IOS_HOST_AND_MSG.match(after_ts)
    if not host_and_msg:
        if not has_pri:
            return _make_cisco_fallback(raw, source_ip, received_at, "missing_pri")
        return _make_cisco_fallback(raw, source_ip, received_at, "unsupported_format")

    body_match = RE_CISCO_BODY.match(host_and_msg.group("body"))
    if not body_match:
        return _make_cisco_fallback(raw, source_ip, received_at, "unsupported_format")

    hostname = host_and_msg.group("host") or source_ip
    fac = body_match.group("fac")
    vsev = int(body_match.group("vsev"))
    code = body_match.group("code")
    mnemonic = body_match.group("mnemonic")
    msg = body_match.group("msg")

    return _build_cisco_event(
        raw=raw,
        source_ip=source_ip,
        received_at=received_at,
        event_timestamp=event_timestamp,
        timestamp_inferred=timestamp_inferred,
        timestamp_origin=timestamp_origin,
        hostname=hostname,
        card_location=None,
        facility=facility,
        pri_severity=pri_severity,
        program=fac,
        mnemonic=mnemonic,
        vendor_severity=vsev,
        fac=fac,
        code=code,
        msg=msg,
    )


def parse_cisco_syslog(
    raw: str,
    source_ip: str = "127.0.0.1",
    *,
    received_at: Optional[datetime] = None,
    source_timezone: Optional[tzinfo] = None,
) -> AlertEvent:
    """Giải mã và chuẩn hóa bản tin Syslog Cisco IOS XR, IOS và Nexus thành AlertEvent.

    Tham số:
        raw: Chuỗi bản tin syslog thô.
        source_ip: Địa chỉ IP nguồn gửi gói tin (IPv4/IPv6).
        received_at: Thời điểm hệ thống tiếp nhận (timezone-aware; mặc định UTC now).
        source_timezone: Múi giờ mặc định khi log thiếu offset (mặc định UTC).
    """
    if not isinstance(raw, str):
        raise TypeError(f"raw must be str, got {type(raw).__name__}")

    try:
        source_ip = str(ipaddress.ip_address(source_ip.strip()))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid source_ip: {source_ip}") from exc

    if received_at is None:
        received_at = datetime.now(timezone.utc)
    else:
        if not isinstance(received_at, datetime):
            raise TypeError("received_at must be a datetime object")
        if received_at.tzinfo is None or received_at.tzinfo.utcoffset(received_at) is None:
            raise ValueError("received_at must be timezone-aware")
        received_at = received_at.astimezone(timezone.utc)

    if source_timezone is None:
        source_timezone = timezone.utc

    if len(raw) == 0:
        return _make_cisco_fallback(raw, source_ip, received_at, "empty_input")

    if len(raw.encode("utf-8")) > MAX_CISCO_PAYLOAD_BYTES:
        return _make_cisco_fallback(raw, source_ip, received_at, "payload_too_large")

    if raw.endswith("\r\n"):
        work_raw = raw[:-2]
    elif raw.endswith("\n"):
        work_raw = raw[:-1]
    else:
        work_raw = raw

    if "\x00" in work_raw or "\r" in work_raw or "\n" in work_raw:
        return _make_cisco_fallback(raw, source_ip, received_at, "malformed_header")

    for ch in work_raw:
        if ord(ch) < 32:
            return _make_cisco_fallback(raw, source_ip, received_at, "malformed_header")

    if RE_FORTINET_KV.match(work_raw):
        return _make_cisco_fallback(raw, source_ip, received_at, "unsupported_format")

    facility: Optional[int] = None
    pri_severity: Optional[int] = None
    has_pri = False
    after_pri = work_raw

    if work_raw.startswith("<"):
        pri_match = RE_PRI_PREFIX.match(work_raw)
        if not pri_match:
            return _make_cisco_fallback(raw, source_ip, received_at, "invalid_pri")
        pri_str = pri_match.group("pri_str")
        if not RE_VALID_PRI.match(pri_str):
            return _make_cisco_fallback(raw, source_ip, received_at, "invalid_pri")
        pri_val = int(pri_str)
        if pri_val > 191:
            return _make_cisco_fallback(raw, source_ip, received_at, "invalid_pri")
        facility = pri_val // 8
        pri_severity = pri_val % 8
        has_pri = True
        after_pri = pri_match.group("rest")

    # Nhánh 1 (ưu tiên): Cisco IOS XR
    xr_result = _parse_ios_xr(
        raw=raw,
        after_pri=after_pri,
        source_ip=source_ip,
        received_at=received_at,
        source_timezone=source_timezone,
        facility=facility,
        pri_severity=pri_severity,
    )
    if xr_result is not None:
        return xr_result

    # Nhánh 2: Cisco IOS / Nexus
    return _parse_ios_nexus(
        raw=raw,
        after_pri=after_pri,
        has_pri=has_pri,
        source_ip=source_ip,
        received_at=received_at,
        source_timezone=source_timezone,
        facility=facility,
        pri_severity=pri_severity,
    )


class CiscoNormalizer:
    """Adapter chuẩn hóa theo giao diện RawEvent -> AlertEvent (tương thích INTERFACES.md)."""

    vendor: str = "cisco"

    def __init__(self, source_timezone: Optional[tzinfo] = None) -> None:
        self.source_timezone = source_timezone or timezone.utc

    def can_parse(self, raw: RawEvent) -> bool:
        """Nhận diện nhanh bản tin Cisco IOS XR hoặc IOS/Nexus từ RawEvent."""
        text = raw.payload.decode("utf-8", errors="replace").strip()
        if not text:
            return False
        after_pri = text
        if text.startswith("<"):
            m = RE_PRI_PREFIX.match(text)
            if not m:
                return False
            after_pri = m.group("rest")
        if RE_IOS_XR_CARD.match(after_pri) and "%" in after_pri:
            return True
        return bool(re.search(r"%[A-Za-z0-9_-]+-[0-7]-[A-Za-z0-9_-]+\s*:", after_pri))

    def parse(self, raw: RawEvent) -> AlertEvent:
        """Giải mã RawEvent an toàn; không ném exception khi payload có byte lỗi."""
        try:
            text = raw.payload.decode("utf-8")
        except UnicodeDecodeError:
            safe_raw = raw.payload.decode("utf-8", errors="replace")
            return _make_cisco_fallback(safe_raw, raw.source_ip, raw.received_at, "invalid_encoding")
        return parse_cisco_syslog(
            text,
            raw.source_ip,
            received_at=raw.received_at,
            source_timezone=self.source_timezone,
        )
