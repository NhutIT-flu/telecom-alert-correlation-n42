from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(
    title="N42 — Hệ thống phân tích cảnh báo mạng",
    version="0.1.0",
    description="Khung ứng dụng khởi đầu cho dự án N4.2.",
)

app.include_router(health_router, prefix="/api", tags=["Health"])
