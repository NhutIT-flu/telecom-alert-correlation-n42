import asyncio
import logging
from typing import Optional

from app.models.raw_event import RawEvent
from app.receiver.metrics import ReceiverMetrics
from app.receiver.protocol import SyslogUDPProtocol

logger = logging.getLogger(__name__)

DEFAULT_UDP_HOST = "0.0.0.0"
DEFAULT_UDP_PORT = 5514
DEFAULT_QUEUE_SIZE = 10_000


class SyslogReceiverServer:
    """Quản lý vòng đời máy chủ tiếp nhận Syslog UDP (Module M1 - BE1)."""

    def __init__(
        self,
        host: str = DEFAULT_UDP_HOST,
        port: int = DEFAULT_UDP_PORT,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        queue: Optional[asyncio.Queue[RawEvent]] = None,
        metrics: Optional[ReceiverMetrics] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.queue_size = queue_size
        self.queue: asyncio.Queue[RawEvent] = queue if queue is not None else asyncio.Queue(maxsize=queue_size)
        self.metrics: ReceiverMetrics = metrics or ReceiverMetrics()
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.protocol: Optional[SyslogUDPProtocol] = None
        self._is_running: bool = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def bound_port(self) -> int:
        """Trả về port thực tế socket đang bind (hữu ích khi bind port 0)."""
        if self.transport:
            sockname = self.transport.get_extra_info("sockname")
            if sockname and len(sockname) > 1:
                return sockname[1]
        return self.port

    async def start(self) -> None:
        """Khởi động lắng nghe UDP socket trên cổng cấu hình."""
        if self._is_running:
            logger.warning("SyslogReceiverServer is already running on %s:%d", self.host, self.port)
            return

        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: SyslogUDPProtocol(queue=self.queue, metrics=self.metrics),
            local_addr=(self.host, self.port),
        )

        self.transport = transport
        self.protocol = protocol
        self._is_running = True
        logger.info("Syslog UDP Receiver listening on %s:%d (queue_size=%d)", self.host, self.port, self.queue_size)

    async def stop(self) -> None:
        """Dừng lắng nghe UDP socket và giải phóng tài nguyên (Graceful Shutdown)."""
        if not self._is_running:
            return

        if self.transport and not self.transport.is_closing():
            self.transport.close()

        self._is_running = False
        logger.info("Syslog UDP Receiver stopped on %s:%d", self.host, self.port)
