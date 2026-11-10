from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class RawEvent:
    """Đại diện cho bản tin sự kiện thô nhận được từ các adapter thu thập (M1).

    Hợp đồng bàn giao giữa BE1 (Ingestion) và BE2 (Parser/Pipeline).
    Không chứa logic parse nghiệp vụ.
    """
    payload: bytes
    source_ip: str
    received_at: datetime
    channel: Literal["udp", "tcp", "file", "api"]

