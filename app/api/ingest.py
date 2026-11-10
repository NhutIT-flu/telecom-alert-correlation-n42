import asyncio
from datetime import datetime, timezone
import logging
from uuid import uuid4

from fastapi import APIRouter, Request, status

from app.models.ingest import IngestRequest, IngestResponse
from app.models.raw_event import RawEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/events", tags=["Ingestion"])

# Hàng đợi trung chuyển trong bộ nhớ (M1 -> BE2 Pipeline)
ingest_queue: asyncio.Queue[RawEvent] = asyncio.Queue(maxsize=10_000)


@router.post(
    "/ingest",
    status_code=status.HTTP_201_CREATED,
    response_model=IngestResponse,
    summary="Tiếp nhận bản tin Syslog qua REST API (FR-02)",
)
async def ingest_event(
    payload: IngestRequest,
    request: Request,
) -> IngestResponse:
    """Tiếp nhận bản tin thô qua REST API, đóng gói thành RawEvent và đẩy vào queue.

    Không thực hiện parse nghiệp vụ tại đây (theo nguyên tắc BE1).
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    now_utc = datetime.now(timezone.utc)
    event_id = uuid4()

    raw_event = RawEvent(
        payload=payload.raw_message.encode("utf-8"),
        source_ip=client_ip,
        received_at=now_utc,
        channel="api",
    )

    try:
        ingest_queue.put_nowait(raw_event)
    except asyncio.QueueFull:
        logger.warning("Ingest queue is full; dropping REST event %s", event_id)

    return IngestResponse(
        status="SUCCESS",
        event_id=event_id,
        received_at=now_utc,
    )

