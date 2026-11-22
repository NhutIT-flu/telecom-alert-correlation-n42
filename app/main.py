from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.ingest import ingest_queue, router as ingest_router
from app.receiver.file_tailer import FileTailer, FileTailerConfig
from app.receiver.server import (
    DEFAULT_UDP_HOST,
    DEFAULT_UDP_PORT,
    SyslogReceiverServer,
)
from app.services.rule_config_loader import load_rule_configuration

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).resolve().parent / "services" / "rules.yaml"


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Khởi tạo cấu hình tập luật
    application.state.rule_configuration = load_rule_configuration(RULES_PATH)

    # Tích hợp Syslog UDP Receiver vào vòng đời ứng dụng (DoD N42-13)
    receiver: Optional[SyslogReceiverServer] = None
    enable_udp = os.getenv("N42_ENABLE_UDP_RECEIVER", "true").lower() in ("true", "1", "yes")

    if enable_udp:
        udp_host = os.getenv("N42_UDP_HOST", DEFAULT_UDP_HOST)
        udp_port = int(os.getenv("N42_UDP_PORT", str(DEFAULT_UDP_PORT)))
        receiver = SyslogReceiverServer(host=udp_host, port=udp_port)
        await receiver.start()
        application.state.syslog_receiver = receiver

    # Tích hợp File Watcher / Tailer vào vòng đời ứng dụng (DoD N42-22)
    file_tailer: Optional[FileTailer] = None
    enable_tailer = os.getenv("N42_ENABLE_FILE_TAILER", "false").lower() in ("true", "1", "yes")
    tailer_path = os.getenv("N42_FILE_TAILER_PATH")

    if enable_tailer and tailer_path:
        lab_dir = os.getenv("N42_LAB_LOGS_DIR")
        config = FileTailerConfig(
            file_path=tailer_path,
            allowed_dir=lab_dir,
            poll_interval=float(os.getenv("N42_FILE_TAILER_POLL_INTERVAL", "0.1")),
            from_beginning=os.getenv("N42_FILE_TAILER_FROM_BEGINNING", "false").lower() in ("true", "1", "yes"),
        )
        file_tailer = FileTailer(config=config, queue=ingest_queue)
        await file_tailer.start()
        application.state.file_tailer = file_tailer

    try:
        yield
    finally:
        if file_tailer and file_tailer.is_running:
            await file_tailer.stop()
        if receiver and receiver.is_running:
            await receiver.stop()


app = FastAPI(
    title="N42 — Hệ thống phân tích cảnh báo mạng",
    version="0.1.0",
    description="Khung ứng dụng khởi đầu cho dự án N4.2.",
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(ingest_router, prefix="/api")
