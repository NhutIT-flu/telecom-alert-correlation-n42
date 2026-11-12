from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.health import router as health_router
from app.services.rule_config_loader import load_rule_configuration

RULES_PATH = Path(__file__).resolve().parent / "services" / "rules.yaml"


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.rule_configuration = load_rule_configuration(RULES_PATH)
    yield


app = FastAPI(
    title="N42 — Hệ thống phân tích cảnh báo mạng",
    version="0.1.0",
    description="Khung ứng dụng khởi đầu cho dự án N4.2.",
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/api", tags=["Health"])
