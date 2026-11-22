"""Unit tests cho File Watcher / File Tailer (Module M1 - BE1 - N42-22).

Bao phủ các bước:
- Bước 1: Khởi tạo cấu hình và Chống Path Traversal (TC-SEC-006).
- Bước 2: Bộ đệm dòng dở dang (Line Buffering & Incomplete Lines).
- Bước 3: Cơ chế xoay tệp (Log Rotation Support).
- Bước 4: Cơ chế thử lại & Chịu lỗi (Retry Policy khi tệp chưa sẵn sàng).
- Bước 5: Kiểm soát hàng đợi có giới hạn & Tránh tràn RAM (Bounded Queue theo NFR-08).
- Bước 6: Tích hợp vòng đời FastAPI Lifespan & E2E Batch Import (FR-03, TC-ING-011).
"""

import asyncio
from pathlib import Path
import time

from fastapi.testclient import TestClient
import pytest

from app.api.ingest import ingest_queue
from app.main import app
from app.models.raw_event import RawEvent
from app.receiver.file_tailer import FileTailer, FileTailerConfig, FileTailerMetrics


class TestFileTailerStep1To6:
    """Bộ kiểm thử toàn diện cho các Bước 1 đến 6 của ticket N42-22."""

    # --------------------------------------------------------------------------
    # BƯỚC 1: Cấu hình an toàn & Chống Path Traversal (TC-SEC-006)
    # --------------------------------------------------------------------------

    def test_step1_path_traversal_relative_rejected(self, tmp_path: Path) -> None:
        """Kiểm tra từ chối đường dẫn chứa ký tự điều hướng '..' (TC-SEC-006)."""
        malicious_path = "../../../etc/passwd"
        with pytest.raises(ValueError, match="Path traversal detected"):
            FileTailerConfig(file_path=malicious_path)

    def test_step1_path_traversal_outside_allowed_dir_rejected(self, tmp_path: Path) -> None:
        """Kiểm tra từ chối tệp nằm ngoài thư mục lab được phép."""
        allowed_dir = tmp_path / "lab_logs"
        allowed_dir.mkdir()

        outside_file = tmp_path / "secret.log"
        outside_file.write_text("secret log data\n", encoding="utf-8")

        # Thử truy cập ra ngoài allowed_dir bằng đường dẫn tương đối
        with pytest.raises(ValueError, match="Path traversal detected"):
            FileTailerConfig(
                file_path="../secret.log",
                allowed_dir=allowed_dir,
            )

    def test_step1_valid_lab_path_accepted(self, tmp_path: Path) -> None:
        """Kiểm tra cấu hình hợp lệ bên trong thư mục lab."""
        lab_dir = tmp_path / "lab_logs"
        lab_dir.mkdir()
        valid_file = lab_dir / "cisco_router.log"
        valid_file.write_text("initial log\n", encoding="utf-8")

        config = FileTailerConfig(file_path="cisco_router.log", allowed_dir=lab_dir)
        assert config.file_path == valid_file.resolve()
        assert config.allowed_dir == lab_dir.resolve()

    # --------------------------------------------------------------------------
    # BƯỚC 2: Xử lý bộ đệm dòng dở dang (Incomplete Line Buffering)
    # --------------------------------------------------------------------------

    def test_step2_incomplete_line_buffering(self, tmp_path: Path) -> None:
        """Kiểm tra chỉ đẩy dòng hoàn chỉnh, giữ dòng dở dang cho tới khi có ký tự xuống dòng."""
        log_file = tmp_path / "device.log"
        log_file.write_bytes(b"")

        queue: asyncio.Queue[RawEvent] = asyncio.Queue()
        metrics = FileTailerMetrics()
        config = FileTailerConfig(file_path=log_file, from_beginning=True)
        tailer = FileTailer(config=config, queue=queue, metrics=metrics)

        # 1. Ghi một dòng hoàn chỉnh và một dòng dở dang (chưa có \n)
        with open(log_file, "ab") as f:
            f.write(b"Line 1: Cisco Link Up\nLine 2: Cisco Port Flap")

        events1 = tailer.read_available()
        assert len(events1) == 1
        assert events1[0].payload == b"Line 1: Cisco Link Up"
        assert events1[0].channel == "file"
        assert tailer.line_buffer == b"Line 2: Cisco Port Flap"
        assert queue.qsize() == 1

        # 2. Ghi tiếp phần đuôi của dòng dở dang kèm ký tự \n
        with open(log_file, "ab") as f:
            f.write(b" - Resolved\n")

        events2 = tailer.read_available()
        assert len(events2) == 1
        assert events2[0].payload == b"Line 2: Cisco Port Flap - Resolved"
        assert tailer.line_buffer == b""
        assert queue.qsize() == 2

        # 3. Ghi dòng có cả ký tự \r\n (chuẩn Windows / Telnet)
        with open(log_file, "ab") as f:
            f.write(b"Line 3: Windows CRLF\r\n")

        events3 = tailer.read_available()
        assert len(events3) == 1
        assert events3[0].payload == b"Line 3: Windows CRLF"
        assert tailer.line_buffer == b""

        tailer.close()

    # --------------------------------------------------------------------------
    # BƯỚC 3: Cơ chế xoay tệp (Log Rotation Support)
    # --------------------------------------------------------------------------

    def test_step3_log_rotation_truncated(self, tmp_path: Path) -> None:
        """Kiểm tra phát hiện xoay tệp khi tệp bị truncate về 0 byte."""
        log_file = tmp_path / "app.log"
        log_file.write_bytes(b"Old Line 1\nOld Line 2\n")

        queue: asyncio.Queue[RawEvent] = asyncio.Queue()
        metrics = FileTailerMetrics()
        config = FileTailerConfig(file_path=log_file, from_beginning=True)
        tailer = FileTailer(config=config, queue=queue, metrics=metrics)

        # Đọc dữ liệu ban đầu
        initial_events = tailer.read_available()
        assert len(initial_events) == 2
        assert metrics.rotations_detected == 0

        # Mô phỏng truncate rotation: xóa sạch file và ghi 2 dòng hoàn toàn mới
        log_file.write_bytes(b"New Line 1\nNew Line 2\n")

        new_events = tailer.read_available()
        assert len(new_events) == 2
        assert new_events[0].payload == b"New Line 1"
        assert new_events[1].payload == b"New Line 2"
        assert metrics.rotations_detected == 1

        tailer.close()

    def test_step3_log_rotation_renamed_and_recreated(self, tmp_path: Path) -> None:
        """Kiểm tra xoay tệp theo cơ chế rename file cũ và tạo file mới."""
        log_file = tmp_path / "rotating.log"
        log_file.write_bytes(b"Log Before Rotation\n")

        queue: asyncio.Queue[RawEvent] = asyncio.Queue()
        metrics = FileTailerMetrics()
        config = FileTailerConfig(file_path=log_file, from_beginning=True)
        tailer = FileTailer(config=config, queue=queue, metrics=metrics)

        # Đọc dữ liệu trước khi xoay
        events1 = tailer.read_available()
        assert len(events1) == 1
        assert events1[0].payload == b"Log Before Rotation"

        tailer.close()

        # Tạo file mới với dữ liệu mới
        rotated_backup = tmp_path / "rotating.log.1"
        log_file.rename(rotated_backup)

        log_file.write_bytes(b"Log After Rotation 1\nLog After Rotation 2\n")

        # Tailer tiếp tục đọc và nhận diện tệp mới
        events2 = tailer.read_available()
        assert len(events2) == 2
        assert events2[0].payload == b"Log After Rotation 1"
        assert events2[1].payload == b"Log After Rotation 2"

        tailer.close()

    # --------------------------------------------------------------------------
    # BƯỚC 4: Cơ chế thử lại khi tệp chưa sẵn sàng (Retry Policy)
    # --------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_step4_file_not_found_retry(self, tmp_path: Path) -> None:
        """Kiểm tra cơ chế thử lại khi tệp chưa tồn tại lúc khởi động."""
        log_file = tmp_path / "delayed.log"
        assert not log_file.exists()

        queue: asyncio.Queue[RawEvent] = asyncio.Queue()
        metrics = FileTailerMetrics()
        config = FileTailerConfig(file_path=log_file, poll_interval=0.05, from_beginning=True)
        tailer = FileTailer(config=config, queue=queue, metrics=metrics)

        await tailer.start()
        assert tailer.is_running is True

        # Chờ tailer chạy retry khi chưa có file
        await asyncio.sleep(0.12)
        assert metrics.open_failures >= 1
        assert queue.empty()

        # Tạo file và ghi dữ liệu
        log_file.write_bytes(b"Delayed Line 1\nDelayed Line 2\n")

        # Chờ tailer tự động phát hiện và đọc
        await asyncio.sleep(0.15)
        assert queue.qsize() == 2
        event1 = queue.get_nowait()
        assert event1.payload == b"Delayed Line 1"
        assert event1.channel == "file"

        await tailer.stop()
        assert tailer.is_running is False

    # --------------------------------------------------------------------------
    # BƯỚC 5: Kiểm soát hàng đợi có giới hạn & Tránh tràn RAM (NFR-08)
    # --------------------------------------------------------------------------

    def test_step5_queue_full_bounded_handling(self, tmp_path: Path) -> None:
        """Kiểm tra xử lý an toàn khi hàng đợi đầy (QueueFull) theo NFR-08."""
        log_file = tmp_path / "bounded.log"
        log_file.write_bytes(b"Msg 1\nMsg 2\nMsg 3\nMsg 4\nMsg 5\n")

        # Hàng đợi chỉ chứa tối đa 2 event
        queue: asyncio.Queue[RawEvent] = asyncio.Queue(maxsize=2)
        metrics = FileTailerMetrics()
        config = FileTailerConfig(file_path=log_file, from_beginning=True)
        tailer = FileTailer(config=config, queue=queue, metrics=metrics)

        events = tailer.read_available()
        assert len(events) == 5
        assert metrics.total_lines_read == 5
        # Queue chỉ chứa 2 dòng đầu do giới hạn dung lượng
        assert queue.qsize() == 2
        # 3 dòng sau bị drop an toàn
        assert metrics.dropped_lines == 3

        tailer.close()

    # --------------------------------------------------------------------------
    # BƯỚC 6: Tích hợp vòng đời FastAPI Lifespan & E2E Batch Import (FR-03)
    # --------------------------------------------------------------------------

    def test_step6_fastapi_lifespan_integration(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Kiểm tra tích hợp vòng đời FastAPI Lifespan và Graceful Shutdown."""
        log_file = tmp_path / "lifespan.log"
        log_file.write_bytes(b"Initial line\n")

        monkeypatch.setenv("N42_ENABLE_UDP_RECEIVER", "false")
        monkeypatch.setenv("N42_ENABLE_FILE_TAILER", "true")
        monkeypatch.setenv("N42_FILE_TAILER_PATH", str(log_file))
        monkeypatch.setenv("N42_LAB_LOGS_DIR", str(tmp_path))
        monkeypatch.setenv("N42_FILE_TAILER_FROM_BEGINNING", "true")
        monkeypatch.setenv("N42_FILE_TAILER_POLL_INTERVAL", "0.05")

        # Dọn sạch ingest_queue trước khi test
        while not ingest_queue.empty():
            ingest_queue.get_nowait()

        with TestClient(app):
            tailer = getattr(app.state, "file_tailer", None)
            assert tailer is not None
            assert tailer.is_running is True

            # Ghi thêm dòng mới vào file
            with open(log_file, "ab") as f:
                f.write(b"Lifespan dynamic event\n")

            time.sleep(0.15)

            # Kiểm tra event đã vào ingest_queue
            assert not ingest_queue.empty()
            event = ingest_queue.get_nowait()
            assert event.payload == b"Initial line"
            assert event.channel == "file"

        # Sau khi đóng client (lifespan shutdown), tailer phải dừng an toàn
        assert tailer.is_running is False

    def test_step6_tc_ing_011_batch_100_lines(self, tmp_path: Path) -> None:
        """TC-ING-011: Nạp batch 100 dòng Syslog chuẩn từ file vào hàng đợi (FR-03)."""
        log_file = tmp_path / "batch_100.log"
        lines = [
            f"<134>Nov 18 12:00:{i:02d} router-01 %LINK-3-UPDOWN: Interface Gi0/{i} changed state to up\n".encode(
                "utf-8"
            )
            for i in range(100)
        ]
        log_file.write_bytes(b"".join(lines))

        queue: asyncio.Queue[RawEvent] = asyncio.Queue(maxsize=10_000)
        metrics = FileTailerMetrics()
        config = FileTailerConfig(file_path=log_file, from_beginning=True)
        tailer = FileTailer(config=config, queue=queue, metrics=metrics)

        events = tailer.read_available()
        assert len(events) == 100
        assert queue.qsize() == 100
        assert metrics.total_lines_read == 100
        assert metrics.dropped_lines == 0

        first_event = queue.get_nowait()
        assert b"Interface Gi0/0" in first_event.payload
        assert first_event.channel == "file"

        tailer.close()
