"""File Watcher / File Tailer Adapter (Module M1 - BE1).

Chịu trách nhiệm theo dõi và đọc liên tục các dòng log mới phát sinh từ tệp
trong môi trường lab, xử lý bộ đệm dòng dở dang, hỗ trợ xoay tệp (log rotation),
và đóng gói thành RawEvent nạp vào hàng đợi bất đồng bộ.
Truy vết: FR-03, AC-01/07, TC-ING-011..013, TC-SEC-006.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple, Union

from app.models.raw_event import RawEvent

logger = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL = 0.1  # Giây
DEFAULT_MAX_LINE_LENGTH = 65536  # 64 KB
DEFAULT_SOURCE_IP = "127.0.0.1"


@dataclass
class FileTailerConfig:
    """Cấu hình cho FileTailer với kiểm tra an toàn đường dẫn."""

    file_path: Union[str, Path]
    allowed_dir: Optional[Union[str, Path]] = None
    poll_interval: float = DEFAULT_POLL_INTERVAL
    from_beginning: bool = False
    source_ip: str = DEFAULT_SOURCE_IP
    max_line_length: int = DEFAULT_MAX_LINE_LENGTH

    def __post_init__(self) -> None:
        """Thẩm định cấu hình và kiểm tra chống Path Traversal (TC-SEC-006)."""
        raw_path = Path(self.file_path)

        if self.allowed_dir is not None:
            resolved_allowed = Path(self.allowed_dir).resolve()
            # Nếu path tương đối, ghép với allowed_dir để kiểm tra
            target_path = (resolved_allowed / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()

            try:
                target_path.relative_to(resolved_allowed)
            except ValueError:
                raise ValueError(
                    f"Path traversal detected: '{self.file_path}' nằm ngoài thư mục cho phép '{self.allowed_dir}'"
                )
            self.file_path = target_path
            self.allowed_dir = resolved_allowed
        else:
            # Nếu không chỉ định allowed_dir, kiểm tra chuỗi path traversal cơ bản
            if ".." in raw_path.parts:
                raise ValueError(f"Path traversal detected: '{self.file_path}' chứa ký tự chuyển hướng thư mục '..'")
            self.file_path = raw_path.resolve()


@dataclass
class FileTailerMetrics:
    """Bộ đếm chỉ số hoạt động của FileTailer."""

    total_lines_read: int = 0
    total_bytes_read: int = 0
    incomplete_lines_buffered: int = 0
    rotations_detected: int = 0
    dropped_lines: int = 0
    open_failures: int = 0


class FileTailer:
    """Bộ thu thập log liên tục từ tệp tin (File Watcher / Tailer)."""

    def __init__(
        self,
        config: FileTailerConfig,
        queue: Optional[object] = None,
        metrics: Optional[FileTailerMetrics] = None,
    ) -> None:
        self.config = config
        self.queue = queue
        self.metrics = metrics or FileTailerMetrics()

        self._file: Optional[BinaryIO] = None
        self._last_offset: int = 0
        self._last_mtime_ns: int = 0
        self._line_buffer: bytes = b""
        self._is_running: bool = False
        self._file_id: Optional[Tuple[int, int]] = None  # (inode/dev hoặc stat snapshot)
        self._task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def current_offset(self) -> int:
        return self._last_offset

    @property
    def line_buffer(self) -> bytes:
        return self._line_buffer

    def _get_file_id(self, stat_result: os.stat_result) -> Tuple[int, int]:
        """Tạo định danh duy nhất cho tệp tin trên hệ điều hành."""
        # Trên Unix/Linux: st_ino và st_dev xác định duy nhất inode
        # Trên Windows: st_ino có thể là 0, kết hợp st_mtime_ns và st_ctime_ns
        ino = getattr(stat_result, "st_ino", 0)
        dev = getattr(stat_result, "st_dev", 0)
        if ino == 0:
            mtime = int(stat_result.st_mtime_ns)
            size = int(stat_result.st_size)
            return (mtime, size)
        return (ino, dev)

    def open_file(self, seek_to_end: Optional[bool] = None) -> bool:
        """Mở tệp tin và định vị con trỏ đọc ban đầu."""
        target_path = Path(self.config.file_path)
        if not target_path.exists() or not target_path.is_file():
            self.metrics.open_failures += 1
            return False

        try:
            f = open(target_path, "rb")
            stat_res = os.fstat(f.fileno())
            self._file_id = self._get_file_id(stat_res)
            self._last_mtime_ns = int(stat_res.st_mtime_ns)

            should_seek_end = seek_to_end if seek_to_end is not None else not self.config.from_beginning
            if should_seek_end:
                f.seek(0, os.SEEK_END)
            else:
                f.seek(0, os.SEEK_SET)

            self._last_offset = f.tell()
            self._file = f
            logger.info("FileTailer opened file %s at offset %d", target_path, self._last_offset)
            return True
        except (OSError, PermissionError) as err:
            logger.warning("FileTailer could not open %s: %s", target_path, err)
            self.metrics.open_failures += 1
            return False

    def close(self) -> None:
        """Đóng tệp và giải phóng tài nguyên."""
        if self._file and not self._file.closed:
            self._file.close()
        self._file = None
        self._last_offset = 0

    def check_log_rotation(self) -> bool:
        """Phát hiện và xử lý khi tệp log bị xoay (truncate hoặc đổi tên tệp mới)."""
        target_path = Path(self.config.file_path)
        if self._file is None:
            return False

        if not target_path.exists():
            # Tệp có thể vừa bị đổi tên hoặc xóa trong quá trình xoay tệp
            return False

        try:
            curr_stat = os.stat(target_path)
            curr_size = curr_stat.st_size
            curr_mtime = int(curr_stat.st_mtime_ns)

            # Trường hợp 1: Tệp bị thu nhỏ kích thước (truncate rotation) hoặc ghi đè từ đầu
            if curr_size < self._last_offset or (
                self._last_offset > 0 and curr_size <= self._last_offset and curr_mtime != self._last_mtime_ns
            ):
                logger.info(
                    "Log rotation detected (file truncated/rewritten from %d to %d)",
                    self._last_offset,
                    curr_size,
                )
                self.metrics.rotations_detected += 1
                self._file.seek(0, os.SEEK_SET)
                self._last_offset = 0
                self._last_mtime_ns = curr_mtime
                self._line_buffer = b""
                return True

            # Trường hợp 2: Tệp bị thay thế bằng inode/file mới (rename/create rotation)
            curr_id = self._get_file_id(curr_stat)
            if self._file_id is not None and curr_id != self._file_id:
                logger.info("Log rotation detected (file replaced with new identity)")
                self.metrics.rotations_detected += 1
                # Đọc nốt phần còn lại của file cũ
                self._read_lines_from_handle()
                self._file.close()
                self._file = None
                # Mở file mới từ đầu (offset = 0)
                return self.open_file(seek_to_end=False)

        except (OSError, PermissionError) as err:
            logger.debug("Stat failed during rotation check: %s", err)

        return False

    def _read_lines_from_handle(self) -> List[RawEvent]:
        """Đọc các byte mới phát sinh từ file handle hiện tại và tách dòng."""
        if self._file is None or self._file.closed:
            return []

        self._file.seek(self._last_offset)
        new_data = self._file.read()
        if not new_data:
            return []

        self._last_offset = self._file.tell()
        try:
            stat_after = os.fstat(self._file.fileno())
            self._last_mtime_ns = int(stat_after.st_mtime_ns)
        except OSError:
            pass
        self.metrics.total_bytes_read += len(new_data)

        # Ghép nối với bộ đệm dòng dở dang trước đó (Line Buffering)
        data = self._line_buffer + new_data
        lines = data.split(b"\n")

        # Phần tử cuối cùng là dòng chưa có ký tự xuống dòng -> lưu vào buffer
        self._line_buffer = lines[-1]
        if self._line_buffer:
            self.metrics.incomplete_lines_buffered = len(self._line_buffer)
        else:
            self.metrics.incomplete_lines_buffered = 0

        # Tất cả các phần tử trước phần tử cuối là các dòng hoàn chỉnh
        events: List[RawEvent] = []
        now = datetime.now(timezone.utc)

        for raw_line in lines[:-1]:
            clean_line = raw_line.rstrip(b"\r")
            if not clean_line:
                # Bỏ qua dòng trống theo chuẩn xử lý Syslog
                continue

            event = RawEvent(
                payload=clean_line,
                source_ip=self.config.source_ip,
                received_at=now,
                channel="file",
            )
            self.metrics.total_lines_read += 1
            events.append(event)

            # Đẩy vào queue nếu có
            if self.queue is not None:
                self._enqueue_event(event)

        return events

    def _enqueue_event(self, event: RawEvent) -> bool:
        """Đẩy event vào queue có kiểm soát dung lượng (Bounded Queue)."""
        if self.queue is None:
            return False

        try:
            # Thử put_nowait nếu queue là asyncio.Queue
            if hasattr(self.queue, "full") and self.queue.full():
                self.metrics.dropped_lines += 1
                logger.warning("Ingest queue full: dropped file log line: %s", event.payload[:40])
                return False
            if hasattr(self.queue, "put_nowait"):
                self.queue.put_nowait(event)
                return True
        except Exception as err:
            self.metrics.dropped_lines += 1
            logger.warning("Could not enqueue RawEvent: %s", err)
            return False
        return False

    def read_available(self) -> List[RawEvent]:
        """Xử lý đọc toàn bộ dữ liệu log có sẵn tại thời điểm hiện tại.

        Hàm đồng bộ an toàn, thuận tiện cho unit test và kiểm tra định kỳ.
        """
        # Kiểm tra rotation trước khi đọc
        if self._file is not None:
            self.check_log_rotation()

        # Mở file nếu chưa mở
        if self._file is None:
            if not self.open_file():
                return []

        return self._read_lines_from_handle()

    async def start(self) -> None:
        """Khởi động tác vụ nền theo dõi tệp (File Tailer Background Task)."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("FileTailer background task started for %s", self.config.file_path)

    async def stop(self) -> None:
        """Dừng tác vụ nền và giải phóng tài nguyên (Graceful Shutdown)."""
        if not self._is_running:
            return
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        self.close()
        logger.info("FileTailer background task stopped for %s", self.config.file_path)

    async def _run_loop(self) -> None:
        """Vòng lặp đọc tệp bất đồng bộ kèm cơ chế thử lại (Retry Loop)."""
        while self._is_running:
            try:
                self.read_available()
            except Exception as err:
                logger.warning("Error in FileTailer loop for %s: %s", self.config.file_path, err)

            try:
                await asyncio.sleep(self.config.poll_interval)
            except asyncio.CancelledError:
                break
