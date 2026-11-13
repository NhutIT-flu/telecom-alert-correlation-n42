"""N42-18: group already-matched events without changing raw evidence."""

from dataclasses import dataclass, field
from datetime import datetime
import math
from threading import Lock
from time import monotonic
from typing import Callable
from uuid import UUID, uuid4

from app.models.alert_event import AlertEvent
from app.models.rule_config import CorrelationRule

GROUP_FIELDS = frozenset(
    {"hostname", "source_ip", "vendor", "mnemonic", "category", "severity", "facility", "program", "parse_status"}
)


@dataclass(frozen=True)
class DedupGroup:
    id: UUID
    rule_id: str
    rule_version: str
    key: tuple[str | int, ...]
    first_seen: datetime
    last_seen: datetime
    evidence_ids: tuple[UUID, ...]

    @property
    def repeat_count(self) -> int:
        return len(self.evidence_ids)


@dataclass(frozen=True)
class DedupResult:
    group: DedupGroup
    expired: tuple[DedupGroup, ...]


@dataclass
class _ActiveGroup:
    started: float
    first_seen: datetime
    last_seen: datetime
    id: UUID = field(default_factory=uuid4)
    evidence: dict[UUID, None] = field(default_factory=dict)


class DeduplicationWindow:
    """One rule/version per instance; caller selects matched events, not this class."""

    def __init__(
        self,
        rule: CorrelationRule,
        *,
        rule_version: str,
        window_seconds: int,
        max_events: int = 10000,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if type(window_seconds) is not int or not 1 <= window_seconds <= 86400:
            raise ValueError("dedup window_seconds must be an integer in 1..86400")
        if type(max_events) is not int or max_events < 1:
            raise ValueError("max_events must be a positive integer")
        if not isinstance(rule_version, str) or not rule_version.strip():
            raise ValueError("rule_version must not be empty")
        if set(rule.group_by) - GROUP_FIELDS:
            raise ValueError("group_by requires supported scalar AlertEvent fields")
        self._rule_id = rule.rule_id
        self._version = rule_version
        self._fields = tuple(rule.group_by)
        self._window = window_seconds
        self._limit = max_events
        self._clock = clock
        self._last_time = -math.inf
        self._lock = Lock()
        # shortcut: state is process-local RAM; add persistence before multi-worker use.
        self._groups: dict[tuple[str | int, ...], _ActiveGroup] = {}
        self._event_count = 0

    def _now(self) -> float:
        now = self._clock()
        if not math.isfinite(now) or now < self._last_time:
            raise ValueError("clock must be finite and monotonic")
        self._last_time = now
        return now

    def _snapshot(self, key: tuple[str | int, ...], group: _ActiveGroup) -> DedupGroup:
        return DedupGroup(
            group.id,
            self._rule_id,
            self._version,
            key,
            group.first_seen,
            group.last_seen,
            tuple(group.evidence),
        )

    def _expire(self, now: float) -> tuple[DedupGroup, ...]:
        expired = []
        for key, group in list(self._groups.items()):
            if now - group.started >= self._window:
                expired.append(self._snapshot(key, group))
                self._event_count -= len(group.evidence)
                del self._groups[key]
        return tuple(expired)

    def expire(self) -> tuple[DedupGroup, ...]:
        """Caller schedules this while idle and persists returned snapshots if needed."""
        with self._lock:
            return self._expire(self._now())

    def add(self, event: AlertEvent) -> DedupResult:
        """Return immutable current/expired groups; retry IDs count once per live key."""
        key = tuple(getattr(event, name) for name in self._fields)
        if any(value is None or (isinstance(value, str) and not value.strip()) for value in key):
            raise ValueError("group_by values must not be null or empty")
        with self._lock:
            now = self._now()
            expired = self._expire(now)
            group = self._groups.get(key)
            if group is not None and event.id in group.evidence:
                return DedupResult(self._snapshot(key, group), expired)
            if self._event_count >= self._limit:
                raise OverflowError("dedup capacity reached; caller must retain the event")
            if group is None:
                group = _ActiveGroup(now, event.received_at, event.received_at)
                self._groups[key] = group
            group.evidence[event.id] = None
            self._event_count += 1
            group.first_seen = min(group.first_seen, event.received_at)
            group.last_seen = max(group.last_seen, event.received_at)
            return DedupResult(self._snapshot(key, group), expired)
