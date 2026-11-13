"""Synthetic fixtures TC-DED-001–008, FR-09/AC-06; no integration claims."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.models.alert_event import AlertEvent
from app.models.rule_config import CorrelationRule
from app.services.deduplication import DeduplicationWindow

BASE = datetime(2026, 11, 13, tzinfo=timezone.utc)


@pytest.fixture
def rule():
    return CorrelationRule.model_validate(
        dict(
            rule_id="SYNTHETIC",
            name="Synthetic",
            window_seconds=60,
            threshold=5,
            group_by=["hostname"],
            match={"vendor": "cisco"},
            action=dict(create_incident=True, incident_severity="MAJOR", title="Synthetic"),
        )
    )


@pytest.fixture
def setup_window(rule):
    clock = [0.0]
    window = DeduplicationWindow(rule, rule_version="0.1.1", window_seconds=10, clock=lambda: clock[0])
    return window, clock


def event(index, *, host="lab-switch", seconds=0, event_seconds=0):
    return AlertEvent(
        id=UUID(int=index),
        received_at=BASE + timedelta(seconds=seconds),
        event_timestamp=BASE + timedelta(seconds=event_seconds),
        source_ip="203.0.113.10",
        hostname=host,
        facility=1,
        severity=3,
        vendor="cisco",
        raw_payload="synthetic raw",
    )


def test_100_events_with_exact_timestamps_and_evidence(setup_window):
    window, clock = setup_window
    inputs = [event(i + 1, seconds=i / 100) for i in range(100)]
    originals = [item.model_dump() for item in inputs]
    groups = []
    for i, item in enumerate(inputs):
        clock[0] = i / 100
        result = window.add(item)
        assert not result.expired
        groups.append(result.group)
    assert len({group.id for group in groups}) == 1
    assert groups[0].repeat_count == 1  # Earlier snapshots must not change.
    assert groups[-1].repeat_count == 100
    assert groups[-1].first_seen == BASE
    assert groups[-1].last_seen == BASE + timedelta(seconds=0.99)
    assert groups[-1].evidence_ids == tuple(item.id for item in inputs)
    assert [item.model_dump() for item in inputs] == originals


def test_different_keys_and_rule_versions(setup_window, rule):
    window, _ = setup_window
    one = window.add(event(1)).group
    two = window.add(event(2, host="other-lab-switch")).group
    other = DeduplicationWindow(rule, rule_version="0.1.2", window_seconds=10).add(event(1)).group
    assert len({one.id, two.id, other.id}) == 3
    assert one.repeat_count == two.repeat_count == other.repeat_count == 1
    assert other.rule_version == "0.1.2"


def test_before_exact_and_after_expiry(setup_window):
    window, clock = setup_window
    one = window.add(event(1)).group
    clock[0] = 9.999
    assert window.add(event(2)).group.id == one.id
    clock[0] = 10
    two = window.add(event(3))
    assert two.group.id != one.id
    assert two.expired[0].repeat_count == 2
    clock[0] = 20.001
    three = window.add(event(4))
    assert three.group.id != two.group.id
    assert three.expired == (two.group,)


def test_retry_and_idle_expiry(setup_window):
    window, clock = setup_window
    one = window.add(event(1)).group
    clock[0] = 5
    assert window.add(event(1, seconds=5)).group == one
    clock[0] = 10
    assert window.expire() == (one,)
    assert window.expire() == ()
    assert window.add(event(1)).group.id != one.id


def test_concurrent_unique_events_and_retries(setup_window):
    window, _ = setup_window
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(window.add, [event(i + 1) for i in range(100)] * 2))
    assert len({result.group.id for result in results}) == 1
    final = window.add(event(1)).group
    assert final.repeat_count == 100
    assert set(final.evidence_ids) == {UUID(int=i + 1) for i in range(100)}


def test_late_timestamps_do_not_backdate_window(setup_window):
    window, clock = setup_window
    first = window.add(event(1, seconds=10, event_seconds=-100)).group
    clock[0] = 9
    last = window.add(event(2, seconds=5, event_seconds=-1000)).group
    assert first.id == last.id
    assert (last.first_seen, last.last_seen) == (BASE + timedelta(seconds=5), BASE + timedelta(seconds=10))
    clock[0] = 10
    assert window.expire() == (last,)


@pytest.mark.parametrize("field", ["interface", "raw_payload", "event_timestamp"])
def test_reject_unavailable_or_unsafe_fields(rule, field):
    rule.group_by = [field]
    with pytest.raises(ValueError):
        DeduplicationWindow(rule, rule_version="v1", window_seconds=10)


@pytest.mark.parametrize(
    "options",
    [
        dict(window_seconds=0),
        dict(window_seconds=True),
        dict(window_seconds=1.5),
        dict(window_seconds=86401),
        dict(max_events=0),
        dict(max_events=True),
        dict(rule_version=" "),
    ],
)
def test_invalid_configuration(rule, options):
    kwargs = dict(rule_version="v1", window_seconds=10)
    kwargs.update(options)
    with pytest.raises(ValueError):
        DeduplicationWindow(rule, **kwargs)


def test_null_key_and_invalid_clock_do_not_add(rule):
    rule.group_by = ["program"]
    clock = [0.0]
    window = DeduplicationWindow(rule, rule_version="v1", window_seconds=10, clock=lambda: clock[0])
    with pytest.raises(ValueError):
        window.add(event(1))
    item = event(1)
    item.program = "synthetic"
    first = window.add(item).group
    for value in [-1, float("nan"), float("inf")]:
        clock[0] = value
        with pytest.raises(ValueError):
            window.add(item)
    clock[0] = 0
    assert window.add(item).group == first


def test_capacity_is_atomic_and_released_on_expiry(rule):
    clock = [0.0]
    window = DeduplicationWindow(rule, rule_version="v1", window_seconds=10, max_events=2, clock=lambda: clock[0])
    window.add(event(1))
    two = window.add(event(2)).group
    with pytest.raises(OverflowError):
        window.add(event(3, host="new-lab-switch"))
    assert window.add(event(2)).group == two
    clock[0] = 10
    result = window.add(event(3, host="new-lab-switch"))
    assert result.expired == (two,)
    assert result.group.repeat_count == 1
