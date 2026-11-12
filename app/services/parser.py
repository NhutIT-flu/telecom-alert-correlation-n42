"""Module Parser: Giải mã và chuẩn hóa bản tin Syslog RFC 3164.

Tuân thủ chặt chẽ:
- docs/N42-15_DESIGN.md
- n42-ai-kit/docs/INTERFACES.md
- Quyết định kỹ thuật: D-01, D-02, D-09
"""

from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timezone, tzinfo
from typing import Optional

from app.models.alert_event import AlertEvent

# Giới hạn dung lượng tối đa cho payload RFC 3164 (đo theo UTF-8 bytes)
MAX_PAYLOAD_BYTES = 1024

# Bản đồ tên tháng tiếng Anh sang số
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

# Regex kiểm tra format không hỗ trợ (để dispatch sang unsupported_format)
RE_FORTINET_KV = re.compile(r"^date=\d{4}-\d{2}-\d{2}\s+time=\d{2}:\d{2}:\d{2}")
RE_ISO_HEADER = re.compile(r"^<(?:\d{1,3})>[12]\d{3}-\d{2}-\d{2}T")

# Regex kiểm tra PRI hợp lệ (0 hoặc 1-191 không có số 0 ở đầu)
RE_PRI_CHECK = re.compile(r"^<(?P<pri_str>[^>]*)>")
RE_VALID_PRI = re.compile(r"^(?:0|[1-9]\d{0,2})$")

# Regex bóc tách header RFC 3164: <PRI>Mmm dd hh:mm:ss HOST MSG
RE_RFC3164_HEADER = re.compile(
    r"^<(?P<pri>0|[1-9]\d{0,2})>"
    r"(?P<month>[A-Za-z]{3})\s+(?P<day>\d{1,2})\s+"
    r"(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\s+"
    r"(?P<host>[^\s]+)"
    r"(?:\s(?P<msg>.*))?$",
    re.DOTALL,
)

# Regex nhận diện định dạng Cisco
RE_CISCO = re.compile(
    r"^%(?P<prog>[A-Za-z0-9_-]+)-(?P<sev>[0-7])-(?P<mnem>[A-Za-z0-9_-]+):\s?(?P<rest>.*)$",
    re.DOTALL,
)

# Regex nhận diện định dạng Huawei (hỗ trợ cả suffix (l))
RE_HUAWEI = re.compile(
    r"^%%01(?P<prog>[A-Za-z0-9_-]+)/(?P<sev>[0-7])/(?P<mnem>[A-Za-z0-9_-]+)(?:\(l\))?:\s?(?P<rest>.*)$",
    re.DOTALL,
)

# Regex nhận diện tag Linux / ứng dụng
RE_LINUX_TAG = re.compile(
    r"^(?P<tag>[a-zA-Z0-9_\.\-]+)(?:\[(?P<pid>\d+)\])?:\s?(?P<rest>.*)$",
    re.DOTALL,
)

# Danh sách tag hệ thống Linux được công nhận theo thiết kế
LINUX_SYSTEM_TAGS = frozenset({"sshd", "kernel", "rsyslogd", "systemd", "sudo", "cron"})


def _make_fallback(
    raw: str,
    source_ip: str,
    received_at: datetime,
    parse_error: str,
) -> AlertEvent:
    """Tạo bản ghi chẩn đoán fallback an toàn khi gặp log lỗi hoặc không hỗ trợ."""
    return AlertEvent(
        received_at=received_at,
        event_timestamp=received_at,
        timestamp_inferred=True,
        source_ip=source_ip,
        hostname=source_ip,
        facility=1,
        severity=6,
        vendor="unknown",
        program=None,
        mnemonic=None,
        category="unknown",
        message=raw,
        raw_payload=raw,
        parse_status="fallback",
        parse_error=parse_error,
    )


def parse_syslog_rfc3164(
    raw: str,
    source_ip: str = "127.0.0.1",
    *,
    received_at: Optional[datetime] = None,
    source_timezone: Optional[tzinfo] = None,
) -> AlertEvent:
    """Giải mã bản tin thô Syslog RFC 3164 thành đối tượng AlertEvent toàn vẹn.

    Tham số:
        raw: Chuỗi bản tin syslog thô.
        source_ip: Địa chỉ IP nguồn (chuẩn hóa IPv4/IPv6).
        received_at: Thời điểm tiếp nhận (bắt buộc timezone-aware nếu truyền vào; mặc định UTC now).
        source_timezone: Múi giờ nguồn để suy diễn năm (mặc định UTC).

    Trả về:
        AlertEvent: Bản ghi chuẩn hóa (parse_status='parsed' hoặc 'fallback').
    """
    # 1. Kiểm tra ranh giới hợp đồng gọi hàm (Contract Boundary)
    if not isinstance(raw, str):
        raise TypeError(f"raw must be str, got {type(raw).__name__}")

    # Kiểm tra địa chỉ source_ip
    try:
        source_ip = str(ipaddress.ip_address(source_ip.strip()))
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid source_ip: {source_ip}") from e

    # Chuẩn hóa thời điểm nhận received_at
    if received_at is None:
        received_at = datetime.now(timezone.utc)
    else:
        if not isinstance(received_at, datetime):
            raise TypeError("received_at must be a datetime object")
        if received_at.tzinfo is None or received_at.tzinfo.utcoffset(received_at) is None:
            raise ValueError("received_at must be timezone-aware")
        received_at = received_at.astimezone(timezone.utc)

    # Chuẩn hóa múi giờ nguồn
    if source_timezone is None:
        source_timezone = timezone.utc

    # 2. Kiểm tra lỗi theo thứ tự ưu tiên (docs/N42-15_DESIGN.md Mục 6)

    # Thứ tự 1: Chuỗi rỗng
    if len(raw) == 0:
        return _make_fallback(raw, source_ip, received_at, "empty_input")

    # Thứ tự 2: Vượt trần dung lượng UTF-8 bytes
    if len(raw.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        return _make_fallback(raw, source_ip, received_at, "payload_too_large")

    # Thứ tự 3: Xử lý ký tự xuống dòng và kiểm tra control characters
    # Cho phép lược bỏ tối đa 1 CRLF hoặc 1 LF ở cuối bản tin
    if raw.endswith("\r\n"):
        work_raw = raw[:-2]
    elif raw.endswith("\n"):
        work_raw = raw[:-1]
    else:
        work_raw = raw

    # Nếu bên trong vẫn còn NUL, CR, hoặc LF -> malformed_header
    if "\x00" in work_raw or "\r" in work_raw or "\n" in work_raw:
        return _make_fallback(raw, source_ip, received_at, "malformed_header")

    # Kiểm tra các ký tự điều khiển ASCII < 32 khác
    for ch in work_raw:
        if ord(ch) < 32:
            return _make_fallback(raw, source_ip, received_at, "malformed_header")

    # Thứ tự 4: Nhận diện định dạng ngoài phạm vi (Unsupported format)
    if RE_FORTINET_KV.match(work_raw) or RE_ISO_HEADER.match(work_raw):
        return _make_fallback(raw, source_ip, received_at, "unsupported_format")

    # Thứ tự 5: Thiếu thẻ mở PRI
    if not work_raw.startswith("<"):
        return _make_fallback(raw, source_ip, received_at, "missing_pri")

    # Thứ tự 6: PRI sai cú pháp hoặc ngoài miền 0..191
    pri_match = RE_PRI_CHECK.match(work_raw)
    if not pri_match:
        return _make_fallback(raw, source_ip, received_at, "invalid_pri")

    pri_str = pri_match.group("pri_str")
    if not RE_VALID_PRI.match(pri_str):
        return _make_fallback(raw, source_ip, received_at, "invalid_pri")

    pri_val = int(pri_str)
    if pri_val > 191:
        return _make_fallback(raw, source_ip, received_at, "invalid_pri")

    # Thứ tự 7: Kiểm tra cấu trúc Header RFC 3164
    header_match = RE_RFC3164_HEADER.match(work_raw)
    if not header_match:
        return _make_fallback(raw, source_ip, received_at, "malformed_header")

    month_str = header_match.group("month")
    if month_str not in MONTH_MAP:
        return _make_fallback(raw, source_ip, received_at, "malformed_header")

    month_num = MONTH_MAP[month_str]
    day = int(header_match.group("day"))
    hour = int(header_match.group("hour"))
    minute = int(header_match.group("min"))
    second = int(header_match.group("sec"))
    hostname = header_match.group("host")
    msg_raw = header_match.group("msg") or ""

    # Thứ tự 8: Kiểm tra tính hợp lệ của ngày/giờ và suy diễn năm
    if hour > 23 or minute > 59 or second > 59:
        return _make_fallback(raw, source_ip, received_at, "invalid_timestamp")

    rec_in_src_tz = received_at.astimezone(source_timezone)
    candidate_years = [rec_in_src_tz.year - 1, rec_in_src_tz.year, rec_in_src_tz.year + 1]

    candidates = []
    for y in candidate_years:
        try:
            cand_dt = datetime(y, month_num, day, hour, minute, second, tzinfo=source_timezone)
            cand_utc = cand_dt.astimezone(timezone.utc)
            distance = abs(cand_utc - received_at)
            candidates.append((distance, cand_utc))
        except ValueError:
            # Ngày không hợp lệ đối với năm ứng viên (ví dụ 31/11 hoặc 29/02 năm không nhuận)
            continue

    if not candidates:
        return _make_fallback(raw, source_ip, received_at, "invalid_timestamp")

    # Chọn ứng viên gần received_at nhất; nếu khoảng cách bằng nhau, ưu tiên mốc sớm hơn
    candidates.sort(key=lambda item: (item[0], item[1]))
    event_timestamp = candidates[0][1]

    # Tính toán chuẩn RFC 5424
    facility = pri_val // 8
    severity = pri_val % 8

    # 3. Phân loại hãng và bóc tách MSG (Vendor Signature Recognition)
    vendor = "unknown"
    program: Optional[str] = None
    mnemonic: Optional[str] = None
    message = msg_raw

    # Thử bóc tách Huawei
    huawei_match = RE_HUAWEI.match(msg_raw)
    if huawei_match:
        vendor = "huawei"
        program = huawei_match.group("prog")
        mnemonic = huawei_match.group("mnem")
        message = huawei_match.group("rest")
    else:
        # Thử bóc tách Cisco
        cisco_match = RE_CISCO.match(msg_raw)
        if cisco_match:
            vendor = "cisco"
            prog = cisco_match.group("prog")
            sev = cisco_match.group("sev")
            mnem = cisco_match.group("mnem")
            program = prog
            mnemonic = f"{prog}-{sev}-{mnem}"
            message = cisco_match.group("rest")
        else:
            # Thử bóc tách Linux hoặc ứng dụng có tag
            linux_match = RE_LINUX_TAG.match(msg_raw)
            if linux_match:
                tag = linux_match.group("tag")
                if tag in LINUX_SYSTEM_TAGS:
                    vendor = "linux"
                else:
                    vendor = "unknown"
                program = tag
                mnemonic = None
                message = linux_match.group("rest")

    return AlertEvent(
        received_at=received_at,
        event_timestamp=event_timestamp,
        timestamp_inferred=True,
        source_ip=source_ip,
        hostname=hostname,
        facility=facility,
        severity=severity,
        vendor=vendor,
        program=program,
        mnemonic=mnemonic,
        category="unknown",
        message=message,
        raw_payload=raw,
        parse_status="parsed",
        parse_error=None,
    )
