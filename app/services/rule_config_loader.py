"""Read and validate one YAML rule configuration file."""

import hashlib
from pathlib import Path
import re

from ruamel.yaml import YAML

from app.models.rule_config import RuleConfiguration


def load_rule_configuration(
    path: Path,
    *,
    supported_event_fields: frozenset[str] | None = None,
    expected_sha256: str | None = None,
) -> RuleConfiguration:
    """Validate one catalog; optional checksum pins exact bytes before YAML parsing."""
    if expected_sha256 is not None and re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256) is None:
        raise ValueError("expected_sha256 must be a 64-character hexadecimal SHA-256 digest")
    content = path.read_bytes()
    if expected_sha256 is not None and hashlib.sha256(content).hexdigest() != expected_sha256.lower():
        raise ValueError("rule configuration SHA-256 mismatch")
    yaml = YAML(typ="safe", pure=True)
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False

    return RuleConfiguration.model_validate(
        yaml.load(content.decode("utf-8")), context={"supported_event_fields": supported_event_fields}
    )
