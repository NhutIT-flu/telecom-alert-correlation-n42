"""Read and validate one YAML rule configuration file."""

from pathlib import Path

from ruamel.yaml import YAML

from app.models.rule_config import RuleConfiguration


def load_rule_configuration(path: Path) -> RuleConfiguration:
    """Raise an I/O, YAML, or validation error if the file cannot be loaded."""
    yaml = YAML(typ="safe", pure=True)
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False

    with path.open(encoding="utf-8") as stream:
        return RuleConfiguration.model_validate(yaml.load(stream))
