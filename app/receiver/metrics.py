from dataclasses import dataclass
from typing import Dict


@dataclass
class ReceiverMetrics:
    """Bộ đếm metrics nội bộ cho UDP Receiver (Module M1)."""

    udp_received_total: int = 0
    udp_dropped_empty: int = 0
    udp_queue_full_drops: int = 0
    udp_errors: int = 0

    def snapshot(self) -> Dict[str, int]:
        """Trả về bản sao các chỉ số hiện tại."""
        return {
            "udp_received_total": self.udp_received_total,
            "udp_dropped_empty": self.udp_dropped_empty,
            "udp_queue_full_drops": self.udp_queue_full_drops,
            "udp_errors": self.udp_errors,
        }

    def reset(self) -> None:
        """Đặt lại các bộ đếm về 0."""
        self.udp_received_total = 0
        self.udp_dropped_empty = 0
        self.udp_queue_full_drops = 0
        self.udp_errors = 0
