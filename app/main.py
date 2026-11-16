from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI

from app.api.health import router as health_router
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

    try:
        yield
    finally:
        if receiver and receiver.is_running:
            await receiver.stop()


app = FastAPI(
    title="N42 — Hệ thống phân tích cảnh báo mạng",
    version="0.1.0",
    description="Khung ứng dụng khởi đầu cho dự án N4.2.",
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api", tags=["Health"])
