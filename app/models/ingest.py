from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Schema yêu cầu cho endpoint REST Ingest (FR-02 / TC-ING-007)."""
    raw_message: str = Field(
        ...,
        min_length=1,
        description="Nội dung chuỗi bản tin syslog thô bắt buộc",
    )
    source: str = Field(
        default="REST_CLIENT",
        description="Định danh nguồn gửi bản tin",
    )


class IngestResponse(BaseModel):
    """Schema phản hồi thành công cho REST Ingest (HTTP 201 Created)."""
    status: str = Field(default="SUCCESS", description="Trạng thái tiếp nhận")
    event_id: UUID = Field(..., description="Mã định danh duy nhất của sự kiện")
    received_at: datetime = Field(..., description="Thời điểm tiếp nhận bản tin UTC")

