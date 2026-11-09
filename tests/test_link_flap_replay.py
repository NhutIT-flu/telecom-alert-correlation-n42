from dataclasses import replace

import pytest

from app.models.rule_config import CorrelationRule
from app.services.rule_config_loader import load_rule_configuration
from tools.replay_link_flap import (
    RULE_ID,
    RULES_PATH,
    replay_link_flap,
    synthetic_events,
)


@pytest.fixture
def rule() -> CorrelationRule:
    config = load_rule_configuration(RULES_PATH)
    return next(rule for rule in config.rules if rule.rule_id == RULE_ID)


@pytest.mark.parametrize(
    ("offsets", "trigger_time"),
    [
        ([0, 10, 20, 30, 40], 40),
        ([0, 10, 20, 30], None),
        ([0, 15, 30, 45, 60], 60),
        ([0, 15, 30, 45, 61], None),
    ],
)
def test_sliding_window(
    rule: CorrelationRule, offsets: list[int], trigger_time: int | None
) -> None:
    events = synthetic_events(offsets)
    incidents = replay_link_flap(events, rule, "lab-version")

    if trigger_time is None:
        assert incidents == []
        return
    (incident,) = incidents
    assert incident.triggered_at_seconds == trigger_time
    assert incident.group == (events[0].hostname, events[0].interface)
    assert incident.evidence_event_ids == [event.event_id for event in events]
    assert incident.rule_version == "lab-version"
    assert incident.severity == rule.action.incident_severity


@pytest.mark.parametrize(
    ("field", "value"), [("interface", "Gi0/2"), ("hostname", "sw-lab-02")]
)
def test_different_groups_do_not_share_threshold(
    rule: CorrelationRule, field: str, value: str
) -> None:
    first = synthetic_events([0, 10, 20])
    second = [
        replace(event, event_id=f"other-{event.event_id}", **{field: value})
        for event in first
    ]
    assert replay_link_flap(first + second, rule, "lab-version") == []


def test_filters_duplicate_reports_and_unrelated_mnemonics(
    rule: CorrelationRule,
) -> None:
    events = synthetic_events([0, 10, 20, 30, 40])
    duplicate = replace(events[1], offset_seconds=15, link_state="DOWN")
    repeated_state = replace(events[1], event_id="repeated", offset_seconds=16)
    other_mnemonic = replace(
        events[2], event_id="other", mnemonic="OTHER", offset_seconds=17
    )

    extra = [duplicate, repeated_state, other_mnemonic]
    assert replay_link_flap(events[:-1] + extra, rule, "lab-version") == []
    (incident,) = replay_link_flap(events + extra, rule, "lab-version")
    assert incident.evidence_event_ids == [event.event_id for event in events]


def test_sustained_flapping_keeps_one_incident_with_all_evidence(
    rule: CorrelationRule,
) -> None:
    events = synthetic_events(list(range(0, 40, 2)))
    (incident,) = replay_link_flap(list(reversed(events)), rule, "lab-version")

    assert incident.triggered_at_seconds == 8
    assert incident.last_seen_seconds == 38
    assert incident.evidence_event_ids == [event.event_id for event in events]


def test_two_bursts_separated_by_a_quiet_window(rule: CorrelationRule) -> None:
    events = synthetic_events([0, 10, 20, 30, 40, 101, 111, 121, 131, 141])

    first, second = replay_link_flap(events, rule, "lab-version")

    assert first.evidence_event_ids == [event.event_id for event in events[:5]]
    assert second.evidence_event_ids == [event.event_id for event in events[5:]]


def test_threshold_and_window_come_from_config(rule: CorrelationRule) -> None:
    draft = rule.model_copy(update={"threshold": 2, "window_seconds": 3})

    (incident,) = replay_link_flap(synthetic_events([0, 3]), draft, "lab-version")
    assert incident.triggered_at_seconds == 3
    assert replay_link_flap(synthetic_events([0, 4]), draft, "lab-version") == []
