"""Schema for the draft N42-17 correlation rule file."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationInfo, field_validator, model_validator

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
EventField = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")]
WindowSeconds = Annotated[int, Field(gt=0, le=86400)]
CountThreshold = Annotated[int, Field(gt=0, le=10000)]
IncidentSeverity = Literal["CRITICAL", "MAJOR", "MINOR", "WARNING", "INFO"]


class _ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RuleCount(_ConfigModel):
    mode: Literal["distinct", "state_changes"]
    field: EventField


class RuleAction(_ConfigModel):
    create_incident: bool
    incident_severity: IncidentSeverity
    title: NonEmptyText = Field(max_length=200)


class CorrelationRule(_ConfigModel):
    rule_id: NonEmptyText = Field(max_length=128)
    name: NonEmptyText = Field(max_length=120)
    description: NonEmptyText | None = Field(default=None, max_length=1000)
    enabled: bool = False
    window_seconds: WindowSeconds
    threshold: CountThreshold
    group_by: list[EventField] = Field(min_length=1)
    match: dict[EventField, NonEmptyText] = Field(min_length=1)
    count: RuleCount | None = None
    action: RuleAction

    @model_validator(mode="after")
    def validate_enabled_fields(self, info: ValidationInfo) -> "CorrelationRule":
        if self.enabled:
            supported = (info.context or {}).get("supported_event_fields")
            if supported is None:
                raise ValueError("enabled rules require supported_event_fields from the producer contract")
            required = set(self.group_by) | set(self.match)
            if self.count is not None:
                required.add(self.count.field)
            missing = required - set(supported)
            if missing:
                raise ValueError(f"enabled rule references unsupported event fields: {', '.join(sorted(missing))}")
        return self

    @field_validator("group_by")
    @classmethod
    def validate_group_fields(cls, fields: list[str]) -> list[str]:
        if len(fields) != len(set(fields)):
            raise ValueError("group_by fields must be unique")
        return fields


class RuleConfiguration(_ConfigModel):
    version: NonEmptyText = Field(max_length=64)
    rules: list[CorrelationRule] = Field(min_length=1)

    @field_validator("rules")
    @classmethod
    def validate_rule_ids(cls, rules: list[CorrelationRule]) -> list[CorrelationRule]:
        rule_ids = [rule.rule_id for rule in rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("rule_id values must be unique")
        return rules
