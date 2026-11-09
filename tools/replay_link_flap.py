"""Replay synthetic Link Flap events using the N42-17 configuration draft."""

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Literal

from app.models.rule_config import CorrelationRule
from app.services.rule_config_loader import load_rule_configuration

RULES_PATH = Path(__file__).resolve().parents[1] / "app/services/rules.yaml"
RULE_ID = "RULE_LINK_FLAP_01"
LinkState = Literal["UP", "DOWN"]


@dataclass(frozen=True)
class LinkEvent:
    event_id: str
    offset_seconds: int
    link_state: LinkState
    hostname: str = "sw-lab-01"
    interface: str = "Gi0/1"
    vendor: str = "cisco"
    mnemonic: str = "LINK-3-UPDOWN"


@dataclass
class ReplayIncident:
    group: tuple[str, ...]
    rule_id: str
    rule_version: str
    severity: str
    title: str
    triggered_at_seconds: int
    last_seen_seconds: int
    evidence_event_ids: list[str]


@dataclass
class _LinkHistory:
    state: LinkState | None = None
    pending: deque[LinkEvent] = field(default_factory=deque)
    incident: ReplayIncident | None = None


def replay_link_flap(
    events: list[LinkEvent], rule: CorrelationRule, rule_version: str
) -> list[ReplayIncident]:
    """Evaluate one explicitly selected rule against a finite lab fixture."""
    if rule.count is None or (rule.count.mode, rule.count.field) != (
        "state_changes",
        "link_state",
    ):
        raise ValueError("Link Flap replay requires state_changes on link_state")
    if set(rule.group_by) != {"hostname", "interface"}:
        raise ValueError("Link Flap replay requires grouping by hostname and interface")
    if rule.match.keys() - {"vendor", "mnemonic"}:
        raise ValueError("Link Flap replay supports matching vendor and mnemonic")

    histories: dict[tuple[str, ...], _LinkHistory] = {}
    seen_ids: set[str] = set()
    incidents: list[ReplayIncident] = []
    for event in sorted(events, key=lambda item: item.offset_seconds):
        if event.event_id in seen_ids or any(
            getattr(event, name) != value for name, value in rule.match.items()
        ):
            continue
        seen_ids.add(event.event_id)
        group = tuple(getattr(event, name) for name in rule.group_by)
        history = histories.setdefault(group, _LinkHistory())

        # Each fixture event reports a change. Count the first report, then
        # require a different state from the last report for this group.
        if history.state == event.link_state:
            continue
        history.state = event.link_state
        cutoff = event.offset_seconds - rule.window_seconds

        if (
            history.incident is not None
            and history.incident.last_seen_seconds >= cutoff
        ):
            history.incident.evidence_event_ids.append(event.event_id)
            history.incident.last_seen_seconds = event.offset_seconds
            continue
        history.incident = None

        while history.pending and history.pending[0].offset_seconds < cutoff:
            history.pending.popleft()
        history.pending.append(event)
        if len(history.pending) >= rule.threshold and rule.action.create_incident:
            history.incident = ReplayIncident(
                group=group,
                rule_id=rule.rule_id,
                rule_version=rule_version,
                severity=rule.action.incident_severity,
                title=rule.action.title,
                triggered_at_seconds=event.offset_seconds,
                last_seen_seconds=event.offset_seconds,
                evidence_event_ids=[item.event_id for item in history.pending],
            )
            incidents.append(history.incident)
            history.pending.clear()
    return incidents


def synthetic_events(offsets: list[int]) -> list[LinkEvent]:
    return [
        LinkEvent(f"lab-{index + 1}", offset, "UP" if index % 2 else "DOWN")
        for index, offset in enumerate(offsets)
    ]


def main() -> None:
    config = load_rule_configuration(RULES_PATH)
    rule = next(rule for rule in config.rules if rule.rule_id == RULE_ID)
    cases = {
        "KB-01-component-positive": [0, 10, 20, 30, 40],
        "below-threshold": [0, 10, 20, 30],
        "inclusive-boundary": [0, 15, 30, 45, 60],
        "outside-window": [0, 15, 30, 45, 61],
        "sustained-flapping": list(range(0, 40, 2)),
    }
    report = {
        "scope": "synthetic component replay",
        "config_sha256": sha256(RULES_PATH.read_bytes()).hexdigest(),
        "config_version": config.version,
        "rule": rule.model_dump(),
        "scenarios": {
            name: {
                "input_offsets_seconds": offsets,
                "incidents": [
                    asdict(incident)
                    for incident in replay_link_flap(
                        synthetic_events(offsets), rule, config.version
                    )
                ],
            }
            for name, offsets in cases.items()
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
