import asyncio
from datetime import datetime, timezone
import logging
from typing import Optional

from app.models.raw_event import RawEvent
from app.receiver.metrics import ReceiverMetrics

logger = logging.getLogger(__name__)


class SyslogUDPProtocol(asyncio.DatagramProtocol):
    """Giao thức xử lý Syslog UDP Socket (Module M1 - BE1).

    Tuân thủ tuyệt đối nguyên tắc non-blocking: không parse nghiệp vụ,
    chỉ đóng gói RawEvent và chuyển tiếp vào bounded queue cho BE2.
    """

    def __init__(
        self,
        queue: asyncio.Queue[RawEvent],
        metrics: Optional[ReceiverMetrics] = None,
    ) -> None:
        self.queue = queue
        self.metrics = metrics or ReceiverMetrics()
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:  # type: ignore[override]
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            self.metrics.udp_received_total += 1

            # TC-ING-002: Kiểm tra biên dưới 0-byte (BVA-01)
            # Datagram rỗng bị drop, không crash, không đẩy vào queue
            if not data:
                self.metrics.udp_dropped_empty += 1
                return

            source_ip = addr[0] if addr else "unknown"
            received_at = datetime.now(timezone.utc)

            event = RawEvent(
                payload=data,
                source_ip=source_ip,
                received_at=received_at,
                channel="udp",
            )

            # Đẩy vào queue không nghẽn (non-blocking)
            try:
                self.queue.put_nowait(event)
            except asyncio.QueueFull:
                self.metrics.udp_queue_full_drops += 1
                logger.warning(
                    "Syslog UDP queue is full (%d items); dropped packet from %s",
                    self.queue.maxsize,
                    source_ip,
                )
        except Exception as exc:
            self.metrics.udp_errors += 1
            logger.error("Unexpected error in datagram_received: %s", exc, exc_info=True)

    def error_received(self, exc: Exception) -> None:
        self.metrics.udp_errors += 1
        logger.error("UDP socket error received: %s", exc)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc:
            self.metrics.udp_errors += 1
            logger.error("UDP connection lost with error: %s", exc)

