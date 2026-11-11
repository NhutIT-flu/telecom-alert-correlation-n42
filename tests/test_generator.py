# -*- coding: utf-8 -*-
"""
Unit Tests cho công cụ sinh dữ liệu giả lập CLI 3 nguồn (tools/generator.py - N42-11).
Kiểm tra:
- Định dạng bản tin RFC 3164 và RFC 5424 đa hãng (Cisco, Huawei, Fortinet, Mixed).
- Tính tất định khi truyền --seed số nguyên hoặc chuỗi kịch bản như KB-08-v1 (FR-13 / TC-REP-001).
- Tuân thủ 100% dải IP Private Lab RFC 1918 & TEST-NET-3 RFC 5737 (AC-08 / TC-SEC-001 / D-09).
- Phát bản tin qua 3 nguồn chuẩn Baseline: UDP Socket, HTTP REST API, và Log File.
- Xử lý biên (rate <= 0, duration limit, send error, request_stop).
"""

from contextlib import contextmanager
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import socket
import tempfile
import threading
from typing import Iterator
import unittest

from tools.generator import DEFAULT_API_URL, FILE_FLUSH_EVERY, SyslogGenerator, main, parse_args


class _IngestHandler(BaseHTTPRequestHandler):
    """Giả lập endpoint POST /api/v1/events/ingest của N42-14 (HTTP/1.1 keep-alive)."""

    protocol_version = "HTTP/1.1"

    def do_POST(self) -> None:  # noqa: N802 - tên hàm do http.server quy định
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        self.server.requests.append(  # type: ignore[attr-defined]
            {"path": self.path, "client_port": self.client_address[1], "body": body}
        )
        data = b'{"status":"SUCCESS"}'
        self.send_response(self.server.reply_status)  # type: ignore[attr-defined]
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if self.server.close_each:  # type: ignore[attr-defined]
            self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Tắt log truy cập để output test gọn."""


@contextmanager
def _run_ingest_server(reply_status: int = 201, close_each: bool = False) -> Iterator[ThreadingHTTPServer]:
    """Chạy server ingest giả lập trên cổng loopback ngẫu nhiên, tự dọn dẹp khi thoát."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _IngestHandler)
    server.daemon_threads = True
    server.requests = []  # type: ignore[attr-defined]
    server.reply_status = reply_status  # type: ignore[attr-defined]
    server.close_each = close_each  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _server_url(server: ThreadingHTTPServer) -> str:
    return f"http://127.0.0.1:{server.server_address[1]}/api/v1/events/ingest"


class SyslogGeneratorTests(unittest.TestCase):
    """Bộ kiểm thử đơn vị cho SyslogGenerator và CLI (N42-11)."""

    def test_vendor_message_formats_rfc3164_and_rfc5424(self) -> None:
        """Kiểm tra định dạng bản tin chuẩn RFC 3164 và RFC 5424 cho từng hãng thiết bị."""
        gen_3164 = SyslogGenerator(seed=42, syslog_format="rfc3164")

        cisco_msg = gen_3164.generate_message(vendor="cisco")
        self.assertTrue(cisco_msg.startswith("<"))
        self.assertTrue(
            any(
                tag in cisco_msg
                for tag in ["%LINK-3-UPDOWN", "%LINEPROTO-5-UPDOWN", "%BGP-5-ADJCHANGE", "%IP-4-DUPADDR"]
            )
        )

        huawei_msg = gen_3164.generate_message(vendor="huawei")
        self.assertTrue(huawei_msg.startswith("<"))
        self.assertIn("%%01", huawei_msg)

        fortinet_msg = gen_3164.generate_message(vendor="fortinet")
        self.assertTrue(fortinet_msg.startswith("<188>"))
        self.assertIn('type="traffic"', fortinet_msg)
        self.assertIn("srcip=10.10.", fortinet_msg)

        # Kiểm tra chuẩn RFC 5424
        gen_5424 = SyslogGenerator(seed=42, syslog_format="rfc5424")
        cisco_5424 = gen_5424.generate_message(vendor="cisco")
        self.assertRegex(cisco_5424, r"^<\d+>1 2026-11-10T12:\d{2}:\d{2}\.\d{3}Z ")
        huawei_5424 = gen_5424.generate_message(vendor="huawei")
        self.assertRegex(huawei_5424, r"^<\d+>1 2026-11-10T12:\d{2}:\d{2}\.\d{3}Z ")
        forti_5424 = gen_5424.generate_message(vendor="fortinet")
        self.assertTrue(forti_5424.startswith("<188>1 2026-11-10T"))

        with self.assertRaises(ValueError):
            gen_3164.generate_message(vendor="unknown_vendor")  # type: ignore[arg-type]

    def test_timestamp_without_seed_and_explicit_datetime(self) -> None:
        """Kiểm tra định dạng timestamp khi không truyền seed hoặc truyền mốc datetime cụ thể."""
        gen_no_seed = SyslogGenerator(seed=None)
        fixed_now = datetime(2026, 11, 9, 8, 5, 3)

        msg_3164 = gen_no_seed.build_cisco_message(now=fixed_now)
        self.assertIn("Nov  9 08:05:03", msg_3164)

        msg_live = gen_no_seed.build_huawei_message()
        self.assertTrue(msg_live.startswith("<"))

        gen_5424_no_seed = SyslogGenerator(seed=None, syslog_format="rfc5424")
        msg_5424 = gen_5424_no_seed.build_cisco_message(now=fixed_now)
        self.assertIn("2026-11-09T08:05:03.000Z", msg_5424)
        msg_5424_live = gen_5424_no_seed.build_fortinet_message()
        self.assertTrue(gen_5424_no_seed.syslog_format == "rfc5424" and msg_5424_live.startswith("<188>1 "))

    def test_deterministic_seed_replay_int_and_string(self) -> None:
        """Kiểm tra tính năng Deterministic Replay (FR-13 / TC-REP-001) với seed số và chuỗi KB-08-v1."""
        gen_a = SyslogGenerator(seed=2026)
        gen_b = SyslogGenerator(seed=2026)
        batch_a = [gen_a.generate_message(vendor="mixed") for _ in range(30)]
        batch_b = [gen_b.generate_message(vendor="mixed") for _ in range(30)]
        self.assertEqual(batch_a, batch_b)

        gen_str_1 = SyslogGenerator(seed="KB-08-v1")
        gen_str_2 = SyslogGenerator(seed="KB-08-v1")
        batch_str_1 = [gen_str_1.generate_message(vendor="mixed") for _ in range(25)]
        batch_str_2 = [gen_str_2.generate_message(vendor="mixed") for _ in range(25)]
        self.assertEqual(batch_str_1, batch_str_2)

    def test_synthetic_ip_compliance(self) -> None:
        """Đảm bảo 100% địa chỉ IP trong bản tin sinh ra thuộc dải Private Lab RFC 1918 hoặc TEST-NET-3 RFC 5737."""
        gen = SyslogGenerator(seed=99)
        ip_regex = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

        for _ in range(100):
            msg = gen.generate_message(vendor="mixed")
            for ip in ip_regex.findall(msg):
                self.assertTrue(
                    ip.startswith("10.")
                    or ip.startswith("192.168.")
                    or ip.startswith("203.0.113.")
                    or ip.startswith("127."),
                    f"Phát hiện IP nằm ngoài dải Lab an toàn: {ip}",
                )

    def test_rate_control_validation_and_error_handling(self) -> None:
        """Kiểm tra điều kiện biên rate <= 0, đếm lỗi khi gửi thất bại, duration và request_stop."""
        gen = SyslogGenerator(seed=11)

        with self.assertRaises(ValueError):
            gen._run_rate_controlled_loop(rate_per_sec=0, count=5, vendor="cisco", send_fn=lambda _: None)

        # Kiểm tra đếm lỗi khi hàm gửi ném ngoại lệ
        def _failing_sender(_: str) -> None:
            raise RuntimeError("Simulated network failure")

        err_stats = gen._run_rate_controlled_loop(
            rate_per_sec=1000,
            count=0,
            vendor="cisco",
            send_fn=_failing_sender,
            duration_sec=0.01,
        )
        self.assertEqual(err_stats["sent"], 0)
        self.assertGreater(err_stats["errors"], 0)

        # Kiểm tra dừng chủ động qua request_stop()
        gen_stop = SyslogGenerator(seed=12)

        def _stop_after_first(_: str) -> None:
            gen_stop.request_stop()

        stop_stats = gen_stop._run_rate_controlled_loop(
            rate_per_sec=100,
            count=50,
            vendor="huawei",
            send_fn=_stop_after_first,
        )
        self.assertEqual(stop_stats["sent"], 1)

    def test_emit_udp_batch_loopback(self) -> None:
        """Kiểm tra phát luồng bản tin qua UDP socket tới cổng loopback nội bộ."""
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver.bind(("127.0.0.1", 0))
        receiver.settimeout(2.0)
        _, port = receiver.getsockname()

        try:
            gen = SyslogGenerator(target_host="127.0.0.1", udp_port=port, seed=10)
            stats = gen.emit_udp_batch(rate_per_sec=1000, count=5, vendor="cisco")

            self.assertEqual(stats["mode"], "udp")
            self.assertEqual(stats["sent"], 5)
            self.assertEqual(stats["errors"], 0)

            received_data, _ = receiver.recvfrom(4096)
            self.assertIn(b"%", received_data)
        finally:
            receiver.close()

    def test_default_api_url_matches_n42_14_contract(self) -> None:
        """Endpoint mặc định phải khớp router N42-14: /api + /v1/events + /ingest."""
        self.assertEqual(DEFAULT_API_URL, "http://127.0.0.1:8000/api/v1/events/ingest")
        self.assertEqual(SyslogGenerator().api_url, DEFAULT_API_URL)
        self.assertEqual(parse_args([]).api_url, DEFAULT_API_URL)

    def test_emit_http_batch_reuses_single_keepalive_connection(self) -> None:
        """50 bản tin HTTP phải đi qua đúng 1 kết nối TCP (tránh TIME_WAIT storm) và đúng payload/đường dẫn."""
        with _run_ingest_server() as server:
            gen = SyslogGenerator(api_url=_server_url(server), seed=7)
            stats = gen.emit_http_batch(rate_per_sec=5000, count=50, vendor="huawei")

        self.assertEqual(stats["mode"], "http")
        self.assertEqual(stats["sent"], 50)
        self.assertEqual(stats["errors"], 0)
        self.assertEqual(len(server.requests), 50)
        self.assertEqual({req["client_port"] for req in server.requests}, {server.requests[0]["client_port"]})
        self.assertEqual({req["path"] for req in server.requests}, {"/api/v1/events/ingest"})
        first_body = server.requests[0]["body"]
        self.assertEqual(first_body["source"], "REST_CLIENT")
        self.assertIn("%%01", first_body["raw_message"])

    def test_emit_http_batch_reconnects_when_server_closes_connection(self) -> None:
        """Server đóng kết nối sau mỗi response: generator tự mở lại, không mất bản tin nào."""
        with _run_ingest_server(close_each=True) as server:
            gen = SyslogGenerator(api_url=_server_url(server), seed=8)
            stats = gen.emit_http_batch(rate_per_sec=5000, count=6, vendor="cisco")

        self.assertEqual(stats["sent"], 6)
        self.assertEqual(stats["errors"], 0)
        self.assertEqual(len({req["client_port"] for req in server.requests}), 6)

    def test_emit_http_batch_counts_non_2xx_as_errors(self) -> None:
        """Mã trả về ngoài 2xx (ví dụ 404 do sai endpoint) phải tính vào errors, không tính là đã gửi."""
        with _run_ingest_server(reply_status=404) as server:
            gen = SyslogGenerator(api_url=_server_url(server), seed=9)
            stats = gen.emit_http_batch(rate_per_sec=5000, count=5, vendor="fortinet")

        self.assertEqual(stats["sent"], 0)
        self.assertEqual(stats["errors"], 5)

    def test_emit_http_batch_counts_unreachable_server_as_errors(self) -> None:
        """Không kết nối được server: không crash, mọi bản tin đều tính vào errors."""
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        _, closed_port = probe.getsockname()
        probe.close()

        gen = SyslogGenerator(api_url=f"http://127.0.0.1:{closed_port}/api/v1/events/ingest", seed=10)
        stats = gen.emit_http_batch(rate_per_sec=1000, count=3, vendor="cisco", timeout=0.5)

        self.assertEqual(stats["sent"], 0)
        self.assertEqual(stats["errors"], 3)

    def test_emit_http_batch_rejects_invalid_url(self) -> None:
        """api_url sai định dạng phải báo ValueError rõ ràng ngay từ đầu."""
        for bad_url in ("ftp://127.0.0.1/ingest", "not-a-url", "http:///path"):
            gen = SyslogGenerator(api_url=bad_url)
            with self.assertRaises(ValueError):
                gen.emit_http_batch(rate_per_sec=100, count=1)

    def test_emit_file_batch(self) -> None:
        """Kiểm tra phát luồng bản tin ghi trực tiếp ra file log."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "simulated_syslog.log"
            gen = SyslogGenerator(file_path=str(log_file), seed=15)

            stats = gen.emit_file_batch(rate_per_sec=1000, count=6, vendor="fortinet")

            self.assertEqual(stats["mode"], "file")
            self.assertEqual(stats["sent"], 6)
            self.assertTrue(log_file.exists())

            lines = log_file.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 6)
            self.assertTrue(all('type="traffic"' in line for line in lines))

    def test_emit_file_batch_flushes_periodically_and_keeps_all_lines(self) -> None:
        """Ghi nhiều hơn FILE_FLUSH_EVERY dòng: flush định kỳ nhưng file cuối cùng vẫn đủ 100% dòng."""
        total = FILE_FLUSH_EVERY * 2 + 50
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "bulk_syslog.log"
            gen = SyslogGenerator(file_path=str(log_file), seed=16)

            stats = gen.emit_file_batch(rate_per_sec=1_000_000, count=total, vendor="mixed")

            self.assertEqual(stats["sent"], total)
            self.assertEqual(stats["errors"], 0)
            self.assertEqual(len(log_file.read_text(encoding="utf-8").splitlines()), total)

    def test_cli_parse_args_and_main_all_modes(self) -> None:
        """Kiểm tra hàm parse_args và luồng thực thi CLI main() trên cả 3 chế độ (file, udp, http)."""
        args_int = parse_args(["--mode", "udp", "--rate", "500", "--vendor", "mixed", "--count", "10", "--seed", "123"])
        self.assertEqual(args_int.mode, "udp")
        self.assertEqual(args_int.rate, 500)
        self.assertEqual(args_int.vendor, "mixed")
        self.assertEqual(args_int.count, 10)
        self.assertEqual(args_int.seed, 123)

        args_str = parse_args(["--mode", "file", "--seed", "KB-08-v1", "--format", "rfc5424"])
        self.assertEqual(args_str.seed, "KB-08-v1")
        self.assertEqual(args_str.format, "rfc5424")

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "cli_out.log"
            exit_file = main(
                [
                    "--mode",
                    "file",
                    "--rate",
                    "1000",
                    "--count",
                    "5",
                    "--vendor",
                    "mixed",
                    "--file-path",
                    str(out_file),
                    "--seed",
                    "KB-08-v1",
                ]
            )
            self.assertEqual(exit_file, 0)
            self.assertEqual(len(out_file.read_text(encoding="utf-8").strip().splitlines()), 5)

        # Kiểm tra main() với chế độ UDP
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver.bind(("127.0.0.1", 0))
        _, udp_port = receiver.getsockname()
        try:
            exit_udp = main(
                [
                    "--mode",
                    "udp",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(udp_port),
                    "--rate",
                    "1000",
                    "--count",
                    "3",
                    "--vendor",
                    "cisco",
                    "--seed",
                    "42",
                ]
            )
            self.assertEqual(exit_udp, 0)
        finally:
            receiver.close()

        # Kiểm tra main() với chế độ HTTP REST (server ingest cục bộ giả lập endpoint N42-14)
        with _run_ingest_server() as server:
            exit_http = main(
                [
                    "--mode",
                    "http",
                    "--api-url",
                    _server_url(server),
                    "--rate",
                    "1000",
                    "--count",
                    "2",
                    "--vendor",
                    "huawei",
                ]
            )
            self.assertEqual(exit_http, 0)
            self.assertEqual(len(server.requests), 2)


if __name__ == "__main__":
    unittest.main()
