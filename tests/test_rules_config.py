import json
import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.error import YAMLError

from app.models.rule_config import RuleConfiguration

from app.services.rule_config_loader import load_rule_configuration

RULES_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "rules.yaml"
FIXTURES_PATH = Path(__file__).parent / "fixtures" / "rules"
VALID_YAML = """\
version: "0.1.0"
rules:
  - rule_id: SAMPLE_01
    name: on
    window_seconds: 1
    threshold: 1
    group_by: [hostname]
    match: {mnemonic: SAMPLE_EVENT}
    action:
      create_incident: true
      incident_severity: CRITICAL
      title: Example
"""


def write_rules(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "rules.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_three_disabled_sample_rules() -> None:
    config = load_rule_configuration(RULES_PATH)
    rules = {rule.rule_id: rule for rule in config.rules}

    assert set(rules) == {
        "RULE_LINK_FLAP_01",
        "RULE_DUAL_PSU_FAILURE_01",
        "RULE_BGP_FLAP_01",
    }
    assert all(not rule.enabled for rule in rules.values())
    link_flap = rules["RULE_LINK_FLAP_01"]
    assert (link_flap.threshold, link_flap.window_seconds) == (5, 60)
    assert link_flap.group_by == ["hostname", "interface"]
    dual_psu = rules["RULE_DUAL_PSU_FAILURE_01"]
    assert dual_psu.threshold == 2
    assert dual_psu.match["mnemonic"] == "POWER_SUPPLY_FAILED"
    assert dual_psu.count is not None
    assert (dual_psu.count.mode, dual_psu.count.field) == ("distinct", "psu_slot")

    bgp = rules["RULE_BGP_FLAP_01"]
    assert bgp.group_by == ["hostname", "peer"]
    assert bgp.match["mnemonic"] == "BGP_SESSION_STATE_CHANGE"
    assert bgp.count is not None
    assert (bgp.count.mode, bgp.count.field) == ("state_changes", "session_state")


def test_loads_yaml_1_2_and_accepts_lower_bound(tmp_path: Path) -> None:
    (rule,) = load_rule_configuration(write_rules(tmp_path, VALID_YAML)).rules

    assert rule.name == "on"
    assert rule.window_seconds == rule.threshold == 1
    assert not rule.enabled


def test_rejects_yaml_with_tab_indentation(tmp_path: Path) -> None:
    path = write_rules(tmp_path, VALID_YAML.replace("  - rule_id", "\t- rule_id"))

    with pytest.raises(YAMLError):
        load_rule_configuration(path)


def test_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    content = VALID_YAML.replace("    threshold: 1", "    threshold: 1\n    threshold: 2")
    path = write_rules(tmp_path, content)

    with pytest.raises(DuplicateKeyError):
        load_rule_configuration(path)


@pytest.mark.parametrize(
    ("field", "original", "value"),
    [
        ("threshold", "1", "0"),
        ("window_seconds", "1", "0"),
        ("threshold", "1", '"five"'),
        ("threshold", "1", '"1"'),
        ("threshold", "1", "true"),
        ("threshold", "1", "1.5"),
        ("window_seconds", "1", "-1"),
        ("window_seconds", "1", '"1"'),
        ("window_seconds", "1", "true"),
        ("window_seconds", "1", "1.5"),
        ("group_by", "[hostname]", "[]"),
        ("group_by", "[hostname]", "[hostname, hostname]"),
    ],
)
def test_rejects_invalid_rule_fields(tmp_path: Path, field: str, original: str, value: str) -> None:
    content = VALID_YAML.replace(f"    {field}: {original}", f"    {field}: {value}")

    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, content))

    assert error.value.errors()[0]["loc"] == ("rules", 0, field)


def test_rejects_duplicate_rule_ids(tmp_path: Path) -> None:
    _, rule_block = VALID_YAML.split("rules:\n", maxsplit=1)

    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, VALID_YAML + rule_block))

    assert error.value.errors()[0]["loc"] == ("rules",)


@pytest.mark.parametrize(
    ("content", "location"),
    [
        ('version: "0.1.0"\nrules: []\n', ("rules",)),
        (
            VALID_YAML.replace("    match: {mnemonic: SAMPLE_EVENT}\n", ""),
            ("rules", 0, "match"),
        ),
        (
            VALID_YAML.replace("match: {mnemonic: SAMPLE_EVENT}", "match: []"),
            ("rules", 0, "match"),
        ),
        (
            VALID_YAML.split("    action:\n", maxsplit=1)[0],
            ("rules", 0, "action"),
        ),
        (
            VALID_YAML.replace("create_incident: true", 'create_incident: "true"'),
            ("rules", 0, "action", "create_incident"),
        ),
        (
            VALID_YAML.replace("      title: Example", "      title: Example\n      priority: 3"),
            ("rules", 0, "action", "priority"),
        ),
        (
            VALID_YAML.replace(
                "    action:",
                "    count: {mode: weighted, field: link_state}\n    action:",
            ),
            ("rules", 0, "count", "mode"),
        ),
        (
            VALID_YAML.replace("    action:", "    count: {mode: state_changes}\n    action:"),
            ("rules", 0, "count", "field"),
        ),
    ],
    ids=[
        "empty-catalog",
        "missing-match",
        "match-list",
        "missing-action",
        "action-quoted-boolean",
        "unknown-action-key",
        "unsupported-count-mode",
        "missing-count-field",
    ],
)
def test_rejects_invalid_rule_file_structure(tmp_path: Path, content: str, location: tuple[str | int, ...]) -> None:
    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, content))

    assert location in {issue["loc"] for issue in error.value.errors()}


def test_loads_vietnamese_text_from_utf8_file(tmp_path: Path) -> None:
    title = "Cổng mạng đổi trạng thái"
    content = VALID_YAML.replace("title: Example", f'title: "{title}"')

    (rule,) = load_rule_configuration(write_rules(tmp_path, content)).rules

    assert rule.action.title == title


@pytest.mark.parametrize(
    "content",
    ["", "- rule_id: SAMPLE_01\n"],
    ids=["empty-document", "list-as-document-root"],
)
def test_rejects_yaml_without_a_configuration_mapping(tmp_path: Path, content: str) -> None:
    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, content))

    assert error.value.errors()[0]["loc"] == ()


def test_reports_missing_yaml_file(tmp_path: Path) -> None:
    path = tmp_path / "missing-rules.yaml"

    with pytest.raises(FileNotFoundError) as error:
        load_rule_configuration(path)

    assert error.value.filename == str(path)


def test_rejects_yaml_file_with_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "rules.yaml"
    path.write_bytes(b'version: "\xff"\n')

    with pytest.raises(UnicodeDecodeError):
        load_rule_configuration(path)


@pytest.mark.parametrize(
    ("original", "replacement", "location"),
    [
        ('version: "0.1.0"', 'version: "   "', ("version",)),
        ("rule_id: SAMPLE_01", 'rule_id: " "', ("rules", 0, "rule_id")),
        ("    name: on", "    enabled: 1\n    name: on", ("rules", 0, "enabled")),
        ("    name: on", "    extra: 1\n    name: on", ("rules", 0, "extra")),
        ("rules:", "extra: 1\nrules:", ("extra",)),
        ("[hostname]", "[host-name]", ("rules", 0, "group_by", 0)),
        ("match: {mnemonic: SAMPLE_EVENT}", "match: {}", ("rules", 0, "match")),
        (
            "match: {mnemonic: SAMPLE_EVENT}",
            'match: {mnemonic: " "}',
            ("rules", 0, "match", "mnemonic"),
        ),
        (
            "match: {mnemonic: SAMPLE_EVENT}",
            "match: {mnemonic: 1}",
            ("rules", 0, "match", "mnemonic"),
        ),
        (
            "    action:",
            "    count: {mode: distinct, field: psu_slot, extra: 1}\n    action:",
            ("rules", 0, "count", "extra"),
        ),
        (
            "    action:",
            "    count: {mode: distinct, field: psu-slot}\n    action:",
            ("rules", 0, "count", "field"),
        ),
    ],
    ids=[
        "blank-version",
        "blank-id",
        "enabled-integer",
        "unknown-rule-key",
        "unknown-catalog-key",
        "invalid-group-field",
        "empty-match",
        "blank-match-value",
        "numeric-match-value",
        "unknown-count-key",
        "invalid-count-field",
    ],
)
def test_rejects_unusable_or_unknown_configuration(
    tmp_path: Path, original: str, replacement: str, location: tuple[str | int, ...]
) -> None:
    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, VALID_YAML.replace(original, replacement)))

    assert location in {issue["loc"] for issue in error.value.errors()}


def test_rejects_duplicate_ids_after_whitespace_normalization(tmp_path: Path) -> None:
    _, rule_block = VALID_YAML.split("rules:\n", maxsplit=1)
    rule_block = rule_block.replace("rule_id: SAMPLE_01", 'rule_id: " SAMPLE_01 "')

    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, VALID_YAML + rule_block))

    assert error.value.errors()[0]["loc"] == ("rules",)


def test_rejects_unsafe_yaml_object_tag(tmp_path: Path) -> None:
    with pytest.raises(YAMLError):
        load_rule_configuration(write_rules(tmp_path, "!!python/object:builtins.object {}"))


def test_review_fixture_references_disabled_catalogs() -> None:
    review = json.loads((FIXTURES_PATH / "review-cases.json").read_text(encoding="utf-8"))
    application = load_rule_configuration(RULES_PATH)
    candidate = load_rule_configuration(FIXTURES_PATH / "candidate-0.1.1.yaml")
    catalog_ids = {rule.rule_id for rule in application.rules}

    assert application.version == review["catalog"]["application"]["version"]
    assert candidate.version == review["catalog"]["candidate"]["version"]
    assert candidate.rules[0].action.incident_severity == "MAJOR"
    assert {rule.rule_id for rule in candidate.rules} == catalog_ids
    assert all(not rule.enabled for rule in candidate.rules)
    for original, proposed in zip(application.rules, candidate.rules, strict=True):
        before, after = original.model_dump(), proposed.model_dump()
        if original.rule_id == "RULE_LINK_FLAP_01":
            assert before["action"]["incident_severity"] == "MAJOR"
            before["action"]["incident_severity"] = "MAJOR"
        assert before == after

    cases = review["cases"]
    assert review["synthetic"] and review["expected_is_not_execution"]
    assert {case["fixture_id"] for case in cases} == {
        *(f"LF-{i:02}" for i in range(1, 8)),
        *(f"PSU-{i:02}" for i in range(1, 8)),
        "BGP-01",
        "BGP-02",
    }
    assert len(cases) == 16
    for case in cases:
        assert case["rule_id"] in catalog_ids
        assert case["synthetic"] and case["version"] == review["fixture_version"]
        assert case["actual_engine"] == "not_run" and case["qa_review"] == "pending"
        assert case["normalized_fields_status"] == "proposed"
        assert case["input"] and case["expected_review"] and case["dependency_tickets"]


@pytest.mark.parametrize(("field", "limit"), [("window_seconds", 86400), ("threshold", 10000)])
def test_enforces_lab_numeric_limits(tmp_path: Path, field: str, limit: int) -> None:
    accepted = VALID_YAML.replace(f"{field}: 1", f"{field}: {limit}")
    assert getattr(load_rule_configuration(write_rules(tmp_path, accepted)).rules[0], field) == limit
    rejected = VALID_YAML.replace(f"{field}: 1", f"{field}: {limit + 1}")
    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, rejected))
    assert ("rules", 0, field) in {e["loc"] for e in error.value.errors()}


@pytest.mark.parametrize("severity", ["CRITICAL", "MAJOR", "MINOR", "WARNING", "INFO"])
def test_accepts_incident_severity_catalog(tmp_path: Path, severity: str) -> None:
    config = load_rule_configuration(write_rules(tmp_path, VALID_YAML.replace("CRITICAL", severity)))
    assert config.rules[0].action.incident_severity == severity


def test_rejects_unknown_incident_severity(tmp_path: Path) -> None:
    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, VALID_YAML.replace("CRITICAL", "MAJRO")))
    assert error.value.errors()[0]["loc"] == ("rules", 0, "action", "incident_severity")


def test_enabled_rule_requires_field_contract(tmp_path: Path) -> None:
    path = write_rules(tmp_path, VALID_YAML.replace("    name: on", "    enabled: true\n    name: on"))
    with pytest.raises(ValidationError):
        load_rule_configuration(path)
    with pytest.raises(ValidationError):
        load_rule_configuration(path, supported_event_fields=frozenset({"hostname"}))
    config = load_rule_configuration(path, supported_event_fields=frozenset({"hostname", "mnemonic"}))
    assert config.rules[0].enabled
    with pytest.raises(ValidationError):
        RuleConfiguration.model_validate(config.model_dump())


def test_enabled_count_field_must_be_supported(tmp_path: Path) -> None:
    content = VALID_YAML.replace("    name: on", "    enabled: true\n    name: on").replace(
        "    action:", "    count: {mode: distinct, field: psu_slot}\n    action:"
    )
    path = write_rules(tmp_path, content)
    with pytest.raises(ValidationError):
        load_rule_configuration(path, supported_event_fields=frozenset({"hostname", "mnemonic"}))
    assert (
        load_rule_configuration(path, supported_event_fields=frozenset({"hostname", "mnemonic", "psu_slot"}))
        .rules[0]
        .enabled
    )


def test_optional_checksum_pins_exact_file_bytes(tmp_path: Path) -> None:
    path = write_rules(tmp_path, VALID_YAML)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert load_rule_configuration(path, expected_sha256=digest).version == "0.1.0"
    path.write_bytes(path.read_bytes() + b"\n# formatting-only change\n")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        load_rule_configuration(path, expected_sha256=digest)


@pytest.mark.parametrize("digest", ["", "xyz", "a" * 63, "g" * 64])
def test_rejects_malformed_checksum(tmp_path: Path, digest: str) -> None:
    with pytest.raises(ValueError, match="expected_sha256"):
        load_rule_configuration(write_rules(tmp_path, VALID_YAML), expected_sha256=digest)


@pytest.mark.parametrize(
    ("field", "limit", "original"),
    [("name", 120, "on"), ("rule_id", 128, "SAMPLE_01"), ("description", 1000, None)],
)
def test_rule_text_limits(tmp_path: Path, field: str, limit: int, original: str | None) -> None:
    def content(size: int) -> str:
        value = "x" * size
        if original is None:
            return VALID_YAML.replace("    name: on", f"    name: on\n    {field}: {value}")
        return VALID_YAML.replace(f"{field}: {original}", f"{field}: {value}")

    assert getattr(load_rule_configuration(write_rules(tmp_path, content(limit))).rules[0], field) == "x" * limit
    with pytest.raises(ValidationError):
        load_rule_configuration(write_rules(tmp_path, content(limit + 1)))


@pytest.mark.parametrize(("original", "limit"), [('version: "0.1.0"', 64), ("title: Example", 200)])
def test_catalog_and_action_text_limits(tmp_path: Path, original: str, limit: int) -> None:
    key = original.split(":", 1)[0]
    load_rule_configuration(write_rules(tmp_path, VALID_YAML.replace(original, f"{key}: {'x' * limit}")))
    with pytest.raises(ValidationError):
        load_rule_configuration(write_rules(tmp_path, VALID_YAML.replace(original, f"{key}: {'x' * (limit + 1)}")))
