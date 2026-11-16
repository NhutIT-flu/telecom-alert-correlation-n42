# -*- coding: utf-8 -*-
"""
Công cụ CLI Sinh dữ liệu giả lập Syslog 3 nguồn (Module M8 - QA & Simulation - N42-11).
Hỗ trợ phát cảnh báo giả lập đa hãng (Cisco, Huawei, Fortinet, Mixed) qua 3 nguồn chuẩn Baseline:
1. UDP Socket (mặc định 127.0.0.1:5514, chuẩn RFC 3164 / RFC 5424)
2. HTTP REST API (POST JSON tới /api/v1/events/ingest theo hợp đồng N42-14, dùng kết nối HTTP keep-alive)
3. Log File (ghi/append trực tiếp dòng log chuẩn phục vụ File Ingestion)

Tuân thủ:
- FR-13, TC-REP-001: Hỗ trợ tham số --seed (số nguyên hoặc chuỗi như KB-08-v1) để tái tạo luồng sự kiện tất định.
- NFR-01, TC-PERF-001..004: Bộ điều tiết tốc độ (Rate Limiter) chính xác cao, đạt >= 1,000 msg/s.
- AC-08, TC-SEC-001..003, D-09: 100% địa chỉ IP thiết bị thuộc dải Private Lab RFC 1918 (10.10.x.x, 192.168.1.x)
  và IP đối tác/minh họa thuộc dải TEST-NET-3 RFC 5737 (203.0.113.0/24).
"""

import argparse
from datetime import datetime
import http.client
import json
import math
from pathlib import Path
import random
import signal
import socket
import sys
import time
from typing import Any, Callable, Dict, List, Literal, Optional, Union
from urllib.parse import urlsplit

VendorChoice = Literal["cisco", "huawei", "fortinet", "mixed"]
ModeChoice = Literal["udp", "http", "api", "rest", "file"]
FormatChoice = Literal["rfc3164", "rfc5424"]
SeedType = Union[int, str]

# Endpoint REST ingest theo hợp đồng N42-14 (router prefix /api + /v1/events + /ingest)
DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1/events/ingest"

# Chỉ flush file log định kỳ để tránh nghẽn Disk I/O ở tốc độ cao; phần còn lại được flush khi đóng file
FILE_FLUSH_EVERY = 200


class HTTPOutcomeUnknown(RuntimeError):
    """POST đã bắt đầu nhưng không nhận được phản hồi đầy đủ; không tự retry."""


def _validate_run_options(rate: float, count: int, duration: Optional[float]) -> None:
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("rate_per_sec phải hữu hạn và lớn hơn 0")
    if count < 0:
        raise ValueError("count không được âm (0 = chạy liên tục)")
    if duration is not None and (not math.isfinite(duration) or duration <= 0):
        raise ValueError("duration phải hữu hạn và lớn hơn 0")


# Danh sách thiết bị giả lập (100% IP thuộc dải Private Lab RFC 1918: 10.10.x.x, 192.168.1.x)
CISCO_DEVICES: List[Dict[str, str]] = [
    {"hostname": "RTR-CORE-HN-01", "ip": "10.10.1.1"},
    {"hostname": "RTR-CORE-HCM-02", "ip": "10.10.1.2"},
    {"hostname": "SW-AGG-DN-01", "ip": "192.168.1.11"},
    {"hostname": "SW-DIST-HN-03", "ip": "192.168.1.12"},
]

HUAWEI_DEVICES: List[Dict[str, str]] = [
    {"hostname": "HW-NE40E-CORE-01", "ip": "10.10.2.1"},
    {"hostname": "HW-NE40E-EDGE-02", "ip": "10.10.2.2"},
    {"hostname": "HW-CE6850-TOR-01", "ip": "192.168.1.21"},
]

FORTINET_DEVICES: List[Dict[str, str]] = [
    {"hostname": "FGT-DC-FW-01", "ip": "10.10.3.1", "devid": "FGT60FTK20000001"},
    {"hostname": "FGT-EDGE-FW-02", "ip": "10.10.3.2", "devid": "FGT60FTK20000002"},
    {"hostname": "FGT-BRANCH-FW-03", "ip": "192.168.1.31", "devid": "FGT60FTK20000003"},
]

CISCO_INTERFACES: List[str] = [
    "GigabitEthernet0/0/0",
    "GigabitEthernet0/0/1",
    "TenGigabitEthernet0/1/0",
    "TenGigabitEthernet0/1/1",
    "Vlan100",
]

HUAWEI_INTERFACES: List[str] = [
    "10GE1/0/1",
    "10GE1/0/2",
    "GE0/0/1",
    "GE0/0/2",
    "Eth-Trunk1",
]

# Dải IP Private Lab (RFC 1918) và TEST-NET-3 (RFC 5737) dùng cho cảnh báo BGP/Firewall giả lập
SYNTHETIC_PEER_IPS: List[str] = [
    "203.0.113.10",
    "203.0.113.25",
    "203.0.113.50",
    "203.0.113.100",
    "192.168.1.250",
    "10.10.99.10",
]


def _parse_seed_arg(value: str) -> SeedType:
    """Chuyển đổi giá trị --seed sang int nếu là chuỗi số, hoặc giữ nguyên chuỗi (ví dụ: 'KB-08-v1')."""
    try:
        return int(value)
    except ValueError:
        return value


class SyslogGenerator:
    """Bộ sinh dữ liệu giả lập Syslog đa hãng qua 3 nguồn (UDP, HTTP REST API, File)."""

    def __init__(
        self,
        target_host: str = "127.0.0.1",
        udp_port: int = 5514,
        api_url: str = DEFAULT_API_URL,
        file_path: str = "logs/simulated_syslog.log",
        seed: Optional[SeedType] = None,
        syslog_format: FormatChoice = "rfc3164",
    ) -> None:
        self.target_host = target_host
        self.udp_port = udp_port
        self.api_url = api_url
        self.file_path = file_path
        self.seed = seed
        self.syslog_format: FormatChoice = syslog_format
        self._rng = random.Random(seed)
        self._seq = 1000
        self._stop_requested = False

    def request_stop(self) -> None:
        """Đặt cờ dừng an toàn khi nhận tín hiệu ngắt (SIGINT / Ctrl+C)."""
        self._stop_requested = True

    def _format_rfc3164_timestamp(self, now: Optional[datetime] = None) -> str:
        """Định dạng dấu thời gian chuẩn RFC 3164 (ví dụ: 'Nov 10 13:05:00')."""
        if now is None:
            if self.seed is not None:
                # Khi chạy với seed cố định, dùng mốc thời gian tất định tăng dần theo seq
                minute = (self._seq // 60) % 60
                second = self._seq % 60
                return f"Nov 10 12:{minute:02d}:{second:02d}"
            now = datetime.now()
        month_abbr = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ][now.month - 1]
        return f"{month_abbr} {now.day:2d} {now.strftime('%H:%M:%S')}"

    def _format_rfc5424_timestamp(self, now: Optional[datetime] = None) -> str:
        """Định dạng dấu thời gian chuẩn RFC 5424 ISO-8601 (ví dụ: '2026-11-10T12:16:41.000Z')."""
        if now is None:
            if self.seed is not None:
                minute = (self._seq // 60) % 60
                second = self._seq % 60
                ms = self._seq % 1000
                return f"2026-11-10T12:{minute:02d}:{second:02d}.{ms:03d}Z"
            now = datetime.now()
        return now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def build_cisco_message(self, now: Optional[datetime] = None) -> str:
        """Sinh bản tin Syslog giả lập chuẩn Cisco IOS (RFC 3164 / RFC 5424)."""
        self._seq += 1
        dev = self._rng.choice(CISCO_DEVICES)
        iface = self._rng.choice(CISCO_INTERFACES)
        peer_ip = self._rng.choice(SYNTHETIC_PEER_IPS)

        templates = [
            (
                187,
                "LINK-3-UPDOWN",
                f"%LINK-3-UPDOWN: Interface {iface}, changed state to down ( peer={peer_ip} )",
            ),
            (
                189,
                "LINEPROTO-5-UPDOWN",
                f"%LINEPROTO-5-UPDOWN: Line protocol on Interface {iface}, changed state to down",
            ),
            (
                189,
                "BGP-5-ADJCHANGE",
                f"%BGP-5-ADJCHANGE: neighbor {peer_ip} Down BGP Notification sent",
            ),
            (
                188,
                "IP-4-DUPADDR",
                f"%IP-4-DUPADDR: Duplicate address {dev['ip']} on {iface}, sourced by 0000.5e00.5301",
            ),
        ]
        pri, msgid, body = self._rng.choice(templates)
        if self.syslog_format == "rfc5424":
            iso_ts = self._format_rfc5424_timestamp(now)
            return f"<{pri}>1 {iso_ts} {dev['hostname']} iosd {self._seq} {msgid} [meta ip=\"{dev['ip']}\"] {body}"
        ts = self._format_rfc3164_timestamp(now)
        return f"<{pri}>{ts} {dev['hostname']} ({dev['ip']}) {self._seq}: {body}"

    def build_huawei_message(self, now: Optional[datetime] = None) -> str:
        """Sinh bản tin Syslog giả lập chuẩn Huawei VRP / NE40E (RFC 3164 / RFC 5424)."""
        self._seq += 1
        dev = self._rng.choice(HUAWEI_DEVICES)
        iface = self._rng.choice(HUAWEI_INTERFACES)
        peer_ip = self._rng.choice(SYNTHETIC_PEER_IPS)

        templates = [
            (
                186,
                "LINK_STATE",
                f"%%01IFNET/2/LINK_STATE(l)[{self._seq}]:The line protocol IP on the interface {iface} "
                f"has entered the DOWN state. (DeviceIp={dev['ip']}, PeerIp={peer_ip})",
            ),
            (
                185,
                "POWER_SUPPLY_FAILED",
                f"%%01DEVM/1/POWER_SUPPLY_FAILED(l)[{self._seq}]:Power supply 1 failed on {dev['hostname']} "
                f"(MgmtIp={dev['ip']}).",
            ),
            (
                188,
                "CPU_TEMP_ALARM",
                f"%%01DEVM/4/CPU_TEMP_ALARM(l)[{self._seq}]:Board temperature exceeds threshold on slot 1 "
                f"(MgmtIp={dev['ip']}).",
            ),
        ]
        pri, msgid, body = self._rng.choice(templates)
        if self.syslog_format == "rfc5424":
            iso_ts = self._format_rfc5424_timestamp(now)
            return f"<{pri}>1 {iso_ts} {dev['hostname']} vrp {self._seq} {msgid} [meta ip=\"{dev['ip']}\"] {body}"
        ts = self._format_rfc3164_timestamp(now)
        return f"<{pri}>{ts} {dev['hostname']} {body}"

    def build_fortinet_message(self, now: Optional[datetime] = None) -> str:
        """Sinh bản tin Syslog giả lập chuẩn Fortinet FortiOS (RFC 3164 / RFC 5424 + KV)."""
        self._seq += 1
        dev = self._rng.choice(FORTINET_DEVICES)
        src_ip = f"10.10.{self._rng.randint(10, 50)}.{self._rng.randint(2, 200)}"
        dst_ip = self._rng.choice(SYNTHETIC_PEER_IPS)
        src_port = self._rng.randint(10000, 60000)
        dst_port = self._rng.choice([22, 80, 443, 3389, 8080])
        action = self._rng.choice(["deny", "drop", "server-rst"])

        kv_body = (
            f"date=2026-11-10 time=12:00:00 "
            f'devname="{dev["hostname"]}" devid="{dev["devid"]}" eventtime={1794280000 + self._seq} '
            f'tz="+0700" logid="0000000013" type="traffic" subtype="forward" level="warning" '
            f"srcip={src_ip} srcport={src_port} dstip={dst_ip} dstport={dst_port} "
            f'proto=6 action="{action}" policyid=101 msg="Synthetic security traffic alert"'
        )
        if self.syslog_format == "rfc5424":
            iso_ts = self._format_rfc5424_timestamp(now)
            return f"<188>1 {iso_ts} {dev['hostname']} fortigate {self._seq} TRAFFIC - {kv_body}"
        ts = self._format_rfc3164_timestamp(now)
        return f"<188>{ts} {dev['hostname']} {kv_body}"

    def generate_message(
        self,
        vendor: VendorChoice = "mixed",
        now: Optional[datetime] = None,
    ) -> str:
        """Sinh 1 bản tin Syslog theo hãng được chọn (cisco, huawei, fortinet, hoặc mixed)."""
        chosen_vendor = vendor
        if vendor == "mixed":
            chosen_vendor = self._rng.choice(["cisco", "huawei", "fortinet"])  # type: ignore[assignment]

        if chosen_vendor == "cisco":
            return self.build_cisco_message(now=now)
        if chosen_vendor == "huawei":
            return self.build_huawei_message(now=now)
        if chosen_vendor == "fortinet":
            return self.build_fortinet_message(now=now)
        raise ValueError(f"Vendor không hợp lệ: {vendor}")

    def _run_rate_controlled_loop(
        self,
        rate_per_sec: int,
        count: int,
        vendor: VendorChoice,
        send_fn: Callable[[str], None],
        duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Vòng lặp phát bản tin điều tiết tốc độ chính xác theo monotonic clock."""
        _validate_run_options(rate_per_sec, count, duration_sec)

        sent_count = 0
        error_count = 0
        unknown_count = 0
        start_time = time.perf_counter()
        interval = 1.0 / float(rate_per_sec)

        while not self._stop_requested:
            # Tính cả bản tin lỗi vào tổng số lượt phát để vòng lặp luôn kết thúc khi đích không phản hồi
            if count > 0 and (sent_count + error_count) >= count:
                break
            if duration_sec is not None and duration_sec > 0:
                if (time.perf_counter() - start_time) >= duration_sec:
                    break

            msg = self.generate_message(vendor=vendor)
            try:
                send_fn(msg)
                sent_count += 1
            except HTTPOutcomeUnknown:
                error_count += 1
                unknown_count += 1
            except Exception:
                error_count += 1

            # Điều tiết tốc độ theo mốc thời gian lý thuyết của gói tin tiếp theo
            target_elapsed = (sent_count + error_count) * interval
            actual_elapsed = time.perf_counter() - start_time
            sleep_duration = target_elapsed - actual_elapsed
            if sleep_duration > 0.002:
                time.sleep(sleep_duration)

        elapsed = max(time.perf_counter() - start_time, 1e-6)
        actual_rate = sent_count / elapsed
        return {
            "sent": sent_count,
            "errors": error_count,
            "attempted": sent_count + error_count,
            "unknown_outcomes": unknown_count,
            "elapsed_sec": round(elapsed, 4),
            "actual_rate": round(actual_rate, 2),
            "vendor": vendor,
        }

    def emit_udp_batch(
        self,
        rate_per_sec: int,
        count: int,
        vendor: Literal["cisco", "huawei", "fortinet", "mixed"] = "mixed",
        duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Phát luồng bản tin Syslog qua UDP socket với tần suất điều tiết chuẩn xác."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1048576)
        except OSError:
            pass

        target_addr = (self.target_host, self.udp_port)

        def _send_udp(message: str) -> None:
            sock.sendto(message.encode("utf-8"), target_addr)

        try:
            result = self._run_rate_controlled_loop(
                rate_per_sec=rate_per_sec,
                count=count,
                vendor=vendor,
                send_fn=_send_udp,
                duration_sec=duration_sec,
            )
            result["mode"] = "udp"
            result["target"] = f"{self.target_host}:{self.udp_port}"
            return result
        finally:
            sock.close()

    def emit_http_batch(
        self,
        rate_per_sec: int,
        count: int,
        vendor: Literal["cisco", "huawei", "fortinet", "mixed"] = "mixed",
        duration_sec: Optional[float] = None,
        timeout: float = 3.0,
    ) -> Dict[str, Any]:
        """Phát luồng bản tin cảnh báo qua HTTP REST API (POST JSON) trên một kết nối keep-alive.

        Dùng chung một http.client.HTTPConnection cho cả đợt phát để tránh cạn kiệt cổng tạm (TIME_WAIT storm).
        Mỗi bản tin chỉ POST một lần. Mất phản hồi được ghi unknown_outcomes (thuộc errors), không tự gửi lại.
        Kết nối mới chỉ dành cho bản tin tiếp theo; chưa có idempotency contract để retry POST an toàn.
        """
        parts = urlsplit(self.api_url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError(f"api_url không hợp lệ (cần http(s)://host[:port]/path): {self.api_url}")

        connection_cls = http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        headers = {"Content-Type": "application/json", "Connection": "keep-alive"}
        connection = connection_cls(parts.hostname, parts.port, timeout=timeout)

        def _send_http(message: str) -> None:
            payload = json.dumps(
                {
                    "raw_message": message,
                    "source": "REST_CLIENT",
                    "vendor": vendor,
                }
            ).encode("utf-8")
            # Lỗi connect xảy ra trước khi POST bắt đầu: không tính là kết quả chưa rõ.
            if connection.sock is None:
                try:
                    connection.connect()
                except (http.client.HTTPException, OSError):
                    connection.close()
                    raise
            try:
                connection.request("POST", path, body=payload, headers=headers)
                response = connection.getresponse()
                response.read()  # đọc hết body để kết nối được tái sử dụng
                status = response.status
                if response.will_close:
                    connection.close()
            except (http.client.HTTPException, OSError) as exc:
                connection.close()
                raise HTTPOutcomeUnknown("Mất phản hồi HTTP; bản tin có thể đã được backend nhận") from exc
            if not 200 <= status < 300:
                raise RuntimeError(f"HTTP {status} từ {self.api_url}")

        try:
            result = self._run_rate_controlled_loop(
                rate_per_sec=rate_per_sec,
                count=count,
                vendor=vendor,
                send_fn=_send_http,
                duration_sec=duration_sec,
            )
        finally:
            connection.close()
        result["mode"] = "http"
        result["target"] = self.api_url
        return result

    def emit_file_batch(
        self,
        rate_per_sec: int,
        count: int,
        vendor: Literal["cisco", "huawei", "fortinet", "mixed"] = "mixed",
        duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Ghi luồng bản tin Syslog ra file văn bản phục vụ kịch bản File Ingestion.

        Chỉ flush mỗi FILE_FLUSH_EVERY dòng; phần còn lại được đẩy xuống đĩa khi đóng file ở cuối đợt.
        """
        out_path = Path(self.file_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("a", encoding="utf-8") as file_handle:
            written = 0

            def _write_line(message: str) -> None:
                nonlocal written
                file_handle.write(message + "\n")
                written += 1
                if written % FILE_FLUSH_EVERY == 0:
                    file_handle.flush()

            result = self._run_rate_controlled_loop(
                rate_per_sec=rate_per_sec,
                count=count,
                vendor=vendor,
                send_fn=_write_line,
                duration_sec=duration_sec,
            )

        result["mode"] = "file"
        result["target"] = str(out_path)
        return result


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Phân tích tham số dòng lệnh cho bộ sinh dữ liệu giả lập CLI."""
    parser = argparse.ArgumentParser(
        description="N42 CLI Syslog Traffic Generator — Bộ sinh dữ liệu giả lập 3 nguồn (UDP, HTTP REST, File)"
    )
    parser.add_argument(
        "--mode",
        choices=["udp", "http", "api", "rest", "file"],
        default="udp",
        help="Nguồn phát bản tin: udp (Syslog UDP), http/api/rest (REST POST), hoặc file (ghi Log File).",
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=500,
        help="Tốc độ phát bản tin mục tiêu (messages/sec, mặc định: 500).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help="Tổng số bản tin cần phát (đặt 0 để chạy liên tục cho đến khi nhấn Ctrl+C hoặc hết --duration).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Thời gian chạy tối đa tính bằng giây (tùy chọn).",
    )
    parser.add_argument(
        "--vendor",
        choices=["cisco", "huawei", "fortinet", "mixed"],
        default="mixed",
        help="Định dạng hãng thiết bị: cisco, huawei, fortinet, hoặc mixed (mặc định: mixed).",
    )
    parser.add_argument(
        "--format",
        choices=["rfc3164", "rfc5424"],
        default="rfc3164",
        help="Định dạng chuẩn Syslog header: rfc3164 hoặc rfc5424 (mặc định: rfc3164).",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Địa chỉ IP máy đích cho chế độ UDP (mặc định: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5514,
        help="Cổng đích cho chế độ UDP (mặc định: 5514).",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=DEFAULT_API_URL,
        help=f"URL endpoint nhận bản tin cho chế độ HTTP REST (mặc định: {DEFAULT_API_URL}).",
    )
    parser.add_argument(
        "--file-path",
        type=str,
        default="logs/simulated_syslog.log",
        help="Đường dẫn file log đầu ra cho chế độ file (mặc định: logs/simulated_syslog.log).",
    )
    parser.add_argument(
        "--seed",
        type=_parse_seed_arg,
        default=None,
        help="Seed ngẫu nhiên (số hoặc chuỗi như KB-08-v1) phục vụ Deterministic Replay (FR-13 / TC-REP-001).",
    )
    args = parser.parse_args(argv)
    try:
        _validate_run_options(args.rate, args.count, args.duration)
        if not 1 <= args.port <= 65535:
            raise ValueError("port phải nằm trong khoảng 1–65535")
    except ValueError as exc:
        parser.error(str(exc))
    return args


def main(argv: Optional[List[str]] = None) -> int:
    """Điểm vào chính của chương trình CLI."""
    args = parse_args(argv)
    generator = SyslogGenerator(
        target_host=args.host,
        udp_port=args.port,
        api_url=args.api_url,
        file_path=args.file_path,
        seed=args.seed,
        syslog_format=args.format,
    )

    interrupted = False

    def _sigint_handler(signum: int, frame: Any) -> None:
        nonlocal interrupted
        interrupted = True
        print("\n[!] Nhận tín hiệu dừng (SIGINT / Ctrl+C). Đang hoàn tất và đóng kết nối an toàn...")
        generator.request_stop()

    previous_sigint = signal.signal(signal.SIGINT, _sigint_handler)

    print("=" * 68)
    print("N42 TELECOM SYSLOG GENERATOR — BỘ SINH DỮ LIỆU GIẢ LẬP 3 NGUỒN")
    print(f"Chế độ (Mode) : {args.mode.upper()} | Chuẩn: {args.format.upper()}")
    print(f"Hãng (Vendor) : {args.vendor}")
    print(f"Tốc độ (Rate) : {args.rate} msg/s | Số lượng (Count): {args.count}")
    if args.seed is not None:
        print(f"Replay Seed   : {args.seed} (Deterministic Mode)")
    print("=" * 68)

    try:
        if args.mode == "udp":
            stats = generator.emit_udp_batch(
                rate_per_sec=args.rate,
                count=args.count,
                vendor=args.vendor,
                duration_sec=args.duration,
            )
        elif args.mode in ("http", "api", "rest"):
            stats = generator.emit_http_batch(
                rate_per_sec=args.rate,
                count=args.count,
                vendor=args.vendor,
                duration_sec=args.duration,
            )
        else:
            stats = generator.emit_file_batch(
                rate_per_sec=args.rate,
                count=args.count,
                vendor=args.vendor,
                duration_sec=args.duration,
            )
    except KeyboardInterrupt:
        print("\n[!] Đã dừng chương trình theo yêu cầu người dùng.")
        return 130
    except (OSError, ValueError, http.client.HTTPException) as exc:
        print(f"[LỖI] Không hoàn tất đợt phát: {exc}", file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGINT, previous_sigint)

    print("-" * 68)
    print(
        f"[HOÀN TẤT] Đích: {stats['target']} | Đã phát: {stats['sent']} bản tin | "
        f"Lỗi: {stats['errors']} (chưa rõ kết quả: {stats['unknown_outcomes']}) | "
        f"Thời gian: {stats['elapsed_sec']}s | "
        f"Thông lượng đạt: {stats['actual_rate']} msg/s"
    )
    print("-" * 68)
    return 130 if interrupted else (1 if stats["errors"] else 0)


if __name__ == "__main__":
    sys.exit(main())
