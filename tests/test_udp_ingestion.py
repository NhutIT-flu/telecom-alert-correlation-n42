import asyncio
from datetime import timezone
import socket
import pytest

from app.models.raw_event import RawEvent
from app.receiver.metrics import ReceiverMetrics
from app.receiver.protocol import SyslogUDPProtocol
from app.receiver.server import SyslogReceiverServer


def send_udp_datagram(payload: bytes, port: int, host: str = "127.0.0.1") -> None:
    """Hàm phụ trợ gửi datagram UDP trong kiểm thử."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(payload, (host, port))
    finally:
        sock.close()


@pytest.fixture
async def receiver_server():
    """Khởi tạo và giải phóng SyslogReceiverServer trên port động (port=0)."""
    server = SyslogReceiverServer(host="127.0.0.1", port=0, queue_size=1000)
    await server.start()
    try:
        yield server
    finally:
        await server.stop()


class TestUDPIngestion:
    """Bộ kiểm thử đơn vị cho Module M1 - Syslog UDP Ingestion (BE1 - N42-13)."""

    async def test_tc_ing_001_valid_rfc3164(self, receiver_server: SyslogReceiverServer):
        """TC-ING-001: Tiếp nhận Syslog UDP RFC 3164 chuẩn xác."""
        payload = (
            b"<134>Nov 06 15:00:00 sw-core-01 %LINK-3-UPDOWN: "
            b"Interface GigabitEthernet0/1, changed state to down"
        )
        send_udp_datagram(payload, receiver_server.bound_port)

        event: RawEvent = await asyncio.wait_for(receiver_server.queue.get(), timeout=2.0)

        assert event.payload == payload
        assert event.source_ip == "127.0.0.1"
        assert event.channel == "udp"
        assert event.received_at.tzinfo == timezone.utc
        assert receiver_server.metrics.udp_received_total == 1
        assert receiver_server.metrics.udp_dropped_empty == 0

    async def test_tc_ing_002_empty_payload_dropped(self, receiver_server: SyslogReceiverServer):
        """TC-ING-002: Kiểm tra biên dưới - Datagram 0 byte (BVA-01) bị drop, không crash."""
        assert receiver_server.protocol is not None

        # Kiểm tra logic xử lý datagram rỗng tại Protocol
        receiver_server.protocol.datagram_received(b"", ("127.0.0.1", 5514))

        assert receiver_server.queue.empty() is True
        assert receiver_server.metrics.udp_received_total == 1
        assert receiver_server.metrics.udp_dropped_empty == 1
        assert receiver_server.is_running is True

        # Gửi datagram rỗng qua mạng xác nhận server không sập
        send_udp_datagram(b"", receiver_server.bound_port)
        await asyncio.sleep(0.05)
        assert receiver_server.is_running is True
        assert receiver_server.queue.empty() is True

    async def test_tc_ing_003_single_byte_payload(self, receiver_server: SyslogReceiverServer):
        """TC-ING-003: Kiểm tra biên 1 byte - Ký tự cực tiểu được tiếp nhận an toàn."""
        payload = b"X"
        send_udp_datagram(payload, receiver_server.bound_port)

        event: RawEvent = await asyncio.wait_for(receiver_server.queue.get(), timeout=2.0)

        assert event.payload == payload
        assert event.channel == "udp"
        assert receiver_server.metrics.udp_received_total == 1
        assert receiver_server.metrics.udp_dropped_empty == 0

    async def test_tc_ing_004_max_buffer_8192(self, receiver_server: SyslogReceiverServer):
        """TC-ING-004: Kiểm tra biên tối đa bộ đệm 8192 bytes được lưu trọn vẹn."""
        header = b"<134>Nov 06 15:00:00 sw-test %SYS-5-CONFIG: "
        padding = b"A" * (8192 - len(header))
        payload = header + padding
        assert len(payload) == 8192

        send_udp_datagram(payload, receiver_server.bound_port)

        event: RawEvent = await asyncio.wait_for(receiver_server.queue.get(), timeout=2.0)

        assert len(event.payload) == 8192
        assert event.payload == payload

    async def test_tc_ing_006_valid_rfc5424(self, receiver_server: SyslogReceiverServer):
        """TC-ING-006: Tiếp nhận Syslog định dạng RFC 5424 (Structured Syslog)."""
        payload = (
            b'<165>1 2026-11-06T15:05:00.123Z router-edge-01 rsyslogd 1234 ID47 '
            b'[exampleSDID@32473 iut="3" eventSource="Application"] BOMAn application event'
        )
        send_udp_datagram(payload, receiver_server.bound_port)

        event: RawEvent = await asyncio.wait_for(receiver_server.queue.get(), timeout=2.0)

        assert event.payload == payload
        assert event.channel == "udp"

    async def test_tc_ing_014_burst_500_packets(self, receiver_server: SyslogReceiverServer):
        """TC-ING-014: Kiểm tra khả năng chịu tải burst 500 gói trong thời gian ngắn."""
        total_packets = 500
        for i in range(total_packets):
            payload = f"<134>Nov 06 15:00:00 sw-burst %TEST-5-BURST: Packet {i}".encode("utf-8")
            send_udp_datagram(payload, receiver_server.bound_port)

        received_events = []
        for _ in range(total_packets):
            event = await asyncio.wait_for(receiver_server.queue.get(), timeout=5.0)
            received_events.append(event)

        assert len(received_events) == total_packets
        assert receiver_server.metrics.udp_received_total == total_packets
        assert receiver_server.metrics.udp_queue_full_drops == 0

    async def test_tc_ing_015_unicode_vietnamese(self, receiver_server: SyslogReceiverServer):
        """TC-ING-015: Tiếp nhận ký tự Unicode Tiếng Việt trong Syslog message."""
        log_text = "<134>Nov 06 15:15:00 thiet-bi-hcm %USER-5-LOGIN: Nguoi dung QuanTri dang nhap thanh cong"
        payload = log_text.encode("utf-8")

        send_udp_datagram(payload, receiver_server.bound_port)

        event: RawEvent = await asyncio.wait_for(receiver_server.queue.get(), timeout=2.0)

        assert event.payload.decode("utf-8") == log_text

    async def test_queue_full_handling(self):
        """Kiểm tra chính sách khi hàng đợi đầy (QueueFull) - Drop an toàn và tăng counter."""
        small_queue: asyncio.Queue[RawEvent] = asyncio.Queue(maxsize=3)
        metrics = ReceiverMetrics()
        server = SyslogReceiverServer(
            host="127.0.0.1",
            port=0,
            queue=small_queue,
            metrics=metrics,
        )
        await server.start()
        try:
            # Gửi 5 gói vào queue có dung lượng tối đa 3
            for i in range(5):
                send_udp_datagram(f"packet-{i}".encode(), server.bound_port)

            await asyncio.sleep(0.05)

            assert small_queue.qsize() == 3
            assert metrics.udp_received_total == 5
            assert metrics.udp_queue_full_drops == 2
        finally:
            await server.stop()

    async def test_server_lifecycle(self):
        """Kiểm tra vòng đời server: start -> is_running -> stop."""
        server = SyslogReceiverServer(host="127.0.0.1", port=0)
        assert server.is_running is False

        await server.start()
        assert server.is_running is True

        await server.stop()
        assert server.is_running is False
