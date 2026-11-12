import asyncio
import logging
import socket
from typing import Optional

from app.models.raw_event import RawEvent
from app.receiver.metrics import ReceiverMetrics
from app.receiver.protocol import SyslogUDPProtocol

logger = logging.getLogger(__name__)

DEFAULT_UDP_HOST = "0.0.0.0"
DEFAULT_UDP_PORT = 5514
DEFAULT_QUEUE_SIZE = 10_000
DEFAULT_SO_RCVBUF = 4 * 1024 * 1024  # 4MB theo NFR-03, TDD v2 Mục 2.1 & tiêu chuẩn DoD N42-13


class SyslogReceiverServer:
    """Quản lý vòng đời máy chủ tiếp nhận Syslog UDP (Module M1 - BE1)."""

    def __init__(
        self,
        host: str = DEFAULT_UDP_HOST,
        port: int = DEFAULT_UDP_PORT,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        queue: Optional[asyncio.Queue[RawEvent]] = None,
        metrics: Optional[ReceiverMetrics] = None,
        so_rcvbuf: int = DEFAULT_SO_RCVBUF,
    ) -> None:
        self.host = host
        self.port = port
        self.queue_size = queue_size
        self.queue: asyncio.Queue[RawEvent] = queue if queue is not None else asyncio.Queue(maxsize=queue_size)
        self.metrics: ReceiverMetrics = metrics or ReceiverMetrics()
        self.so_rcvbuf = so_rcvbuf
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

    @property
    def rcvbuf_size(self) -> Optional[int]:
        """Trả về kích thước thực tế của socket receive buffer (SO_RCVBUF)."""
        if self.transport:
            sock = self.transport.get_extra_info("socket")
            if sock:
                return sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        return None

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

        # Cấu hình SO_RCVBUF tối thiểu 4MB phòng chống tràn đệm tầng nhân hệ điều hành (DoD N42-13)
        sock = transport.get_extra_info("socket")
        if sock and self.so_rcvbuf > 0:
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.so_rcvbuf)
            except OSError as err:
                logger.warning("Could not set SO_RCVBUF to %d: %s", self.so_rcvbuf, err)

        self.transport = transport
        self.protocol = protocol
        self._is_running = True
        logger.info(
            "Syslog UDP Receiver listening on %s:%d (queue_size=%d, SO_RCVBUF=%s)",
            self.host,
            self.port,
            self.queue_size,
            self.rcvbuf_size,
        )

    async def stop(self) -> None:
        """Dừng lắng nghe UDP socket và giải phóng tài nguyên (Graceful Shutdown)."""
        if not self._is_running:
            return

        if self.transport and not self.transport.is_closing():
            self.transport.close()

        self._is_running = False
        logger.info("Syslog UDP Receiver stopped on %s:%d", self.host, self.port)
