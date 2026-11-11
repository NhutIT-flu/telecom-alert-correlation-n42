"""Mô hình dữ liệu AlertEvent theo chuẩn Pydantic v2.

Căn cứ: docs/N42-15_DESIGN.md và n42-ai-kit/docs/INTERFACES.md.
"""

from __future__ import annotations

import ipaddress
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

VendorType = Literal["cisco", "huawei", "fortinet", "linux", "unknown"]
ParseStatusType = Literal["parsed", "fallback"]


class AlertEvent(BaseModel):
    """Thực thể dữ liệu chuẩn hóa đại diện cho một sự kiện cảnh báo viễn thông."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        validate_assignment=True,
    )

    id: UUID = Field(
        default_factory=uuid4, description="Định danh duy nhất của sự kiện"
    )
    schema_version: Literal["1.0"] = "1.0"
    received_at: datetime = Field(description="Thời điểm hệ thống tiếp nhận (UTC)")
    event_timestamp: datetime = Field(
        description="Thời điểm xảy ra sự kiện theo log (UTC)"
    )
    timestamp_inferred: bool = Field(
        default=True,
        description="True nếu năm/múi giờ được suy diễn (mặc định True với RFC 3164 và fallback)",
    )
    source_ip: str = Field(description="Địa chỉ IP nguồn gửi bản tin (transport IP)")
    hostname: str = Field(
        description="Tên thiết bị bóc tách từ header hoặc IP nguồn khi fallback"
    )
    facility: int = Field(
        ge=0, le=23, description="Mã phân loại dịch vụ theo RFC 5424 (0-23)"
    )
    severity: int = Field(
        ge=0, le=7, description="Mức độ nghiêm trọng theo RFC 5424 (0-7)"
    )
    vendor: VendorType = Field(description="Hãng thiết bị viễn thông hoặc unknown")
    program: Optional[str] = Field(
        default=None, description="Tên tiến trình/tag phát sinh cảnh báo"
    )
    mnemonic: Optional[str] = Field(
        default=None, description="Mã nhận dạng sự kiện của hãng"
    )
    category: str = Field(
        default="unknown", description="Phân loại nghiệp vụ chuẩn hóa"
    )
    message: str = Field(
        default="", description="Nội dung thông điệp cảnh báo đã bóc tách"
    )
    raw_payload: str = Field(default="", description="Bản tin gốc đầy đủ nguyên trạng")
    parse_status: ParseStatusType = Field(
        default="parsed", description="Trạng thái bóc tách (parsed hoặc fallback)"
    )
    parse_error: Optional[str] = Field(
        default=None, description="Mã lỗi khi parse_status=fallback"
    )

    @field_validator("facility", "severity", mode="before")
    @classmethod
    def validate_strict_int(cls, v: object) -> int:
        if isinstance(v, bool):
            raise ValueError("Boolean values are not allowed for facility/severity")
        if not isinstance(v, int):
            raise ValueError("facility and severity must be integers")
        return v

    @field_validator("received_at", "event_timestamp", mode="before")
    @classmethod
    def validate_timezone_aware(cls, v: object) -> datetime:
        if not isinstance(v, datetime):
            raise ValueError("Value must be a datetime object")
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("Datetime must be timezone-aware")
        return v.astimezone(timezone.utc)

    @field_validator("source_ip", mode="before")
    @classmethod
    def validate_ip(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("source_ip must be a string")
        try:
            ip = ipaddress.ip_address(v.strip())
            return str(ip)
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {v}") from e

    @property
    def timestamp(self) -> datetime:
        """Thuộc tính tương thích ngược trỏ về event_timestamp."""
        return self.event_timestamp

    @property
    def raw_log(self) -> str:
        """Thuộc tính tương thích ngược trỏ về raw_payload."""
        return self.raw_payload
