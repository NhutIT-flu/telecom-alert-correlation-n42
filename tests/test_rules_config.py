from pathlib import Path

import pytest
from pydantic import ValidationError
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.error import YAMLError

from app.services.rule_config_loader import load_rule_configuration

RULES_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "rules.yaml"
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
    content = VALID_YAML.replace(
        "    threshold: 1", "    threshold: 1\n    threshold: 2"
    )
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
        ("group_by", "[hostname]", "[]"),
        ("group_by", "[hostname]", "[hostname, hostname]"),
    ],
)
def test_rejects_invalid_rule_fields(
    tmp_path: Path, field: str, original: str, value: str
) -> None:
    content = VALID_YAML.replace(f"    {field}: {original}", f"    {field}: {value}")

    with pytest.raises(ValidationError) as error:
        load_rule_configuration(write_rules(tmp_path, content))

    assert error.value.errors()[0]["loc"] == ("rules", 0, field)


def test_rejects_duplicate_rule_ids(tmp_path: Path) -> None:
    _, rule_block = VALID_YAML.split("rules:\n", maxsplit=1)

    with pytest.raises(ValidationError, match="rule_id values must be unique"):
        load_rule_configuration(write_rules(tmp_path, VALID_YAML + rule_block))


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
            VALID_YAML.replace(
                "      title: Example", "      title: Example\n      priority: 3"
            ),
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
            VALID_YAML.replace(
                "    action:", "    count: {mode: state_changes}\n    action:"
            ),
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
def test_rejects_invalid_rule_file_structure(
    tmp_path: Path, content: str, location: tuple[str | int, ...]
) -> None:
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
def test_rejects_yaml_without_a_configuration_mapping(
    tmp_path: Path, content: str
) -> None:
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
