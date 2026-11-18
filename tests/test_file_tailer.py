"""Unit tests cho File Watcher / File Tailer (Module M1 - BE1 - N42-22).

Bao phủ các bước:
- Bước 1: Khởi tạo cấu hình và Chống Path Traversal (TC-SEC-006).
- Bước 2: Bộ đệm dòng dở dang (Line Buffering & Incomplete Lines).
- Bước 3: Cơ chế xoay tệp (Log Rotation Support).
"""

import asyncio
from pathlib import Path
import pytest

from app.models.raw_event import RawEvent
from app.receiver.file_tailer import FileTailer, FileTailerConfig, FileTailerMetrics


class TestFileTailerStep1To3:
    """Bộ kiểm thử cho Bước 1, 2 và 3 của ticket N42-22."""

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

        # Đóng file handle trên tailer để cho phép rename an toàn trên hệ điều hành Windows
        # Hoặc viết dòng chưa đọc vào file cũ, đổi tên sang .log.old và tạo .log mới
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
