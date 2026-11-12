import asyncio
from datetime import datetime, timezone
import logging
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.models.ingest import BatchImportResponse, IngestRequest, IngestResponse
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


@router.post(
    "/import-file",
    status_code=status.HTTP_200_OK,
    response_model=BatchImportResponse,
    summary="Nhập file log batch từ máy khách (FR-03)",
)
async def import_log_file(
    request: Request,
    file: UploadFile = File(..., description="Tệp tin log định dạng text"),
) -> BatchImportResponse:
    """Đọc từng dòng trong file log, chuyển thành RawEvent đưa vào queue.

    Xử lý an toàn: kiểm tra chống Path Traversal (TC-SEC-006), an toàn với file rỗng
    0 byte (TC-ING-013), chịu lỗi dòng hỏng mà không gián đoạn tiến trình (TC-ING-012).
    Không thực hiện parse nghiệp vụ tại đây (theo nguyên tắc BE1).
    """
    filename = file.filename or ""

    # TC-SEC-006: Kiểm tra chống tấn công Path Traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên tệp không hợp lệ: phát hiện dấu hiệu Path Traversal",
        )

    content = await file.read()

    # Bước 3.4 (TC-ING-013): File kích thước 0 byte
    if not content:
        return BatchImportResponse(
            total=0,
            success=0,
            failed=0,
            error_lines=[],
        )

    # Bước 3.5 (TC-ING-011, TC-ING-012): Đọc từng dòng và xử lý dòng lỗi
    raw_lines = content.splitlines()
    total = len(raw_lines)
    success = 0
    failed = 0
    error_lines: list[int] = []

    now_utc = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else "127.0.0.1"

    for line_idx, line in enumerate(raw_lines, 1):
        try:
            decoded = line.decode("utf-8")
            if "\x00" in decoded or not decoded.strip():
                failed += 1
                error_lines.append(line_idx)
                continue

            raw_event = RawEvent(
                payload=line,
                source_ip=client_ip,
                received_at=now_utc,
                channel="file",
            )

            try:
                ingest_queue.put_nowait(raw_event)
            except asyncio.QueueFull:
                logger.warning("Ingest queue full during batch file import at line %d", line_idx)

            success += 1
        except UnicodeDecodeError:
            failed += 1
            error_lines.append(line_idx)

    return BatchImportResponse(
        total=total,
        success=success,
        failed=failed,
        error_lines=error_lines,
    )
