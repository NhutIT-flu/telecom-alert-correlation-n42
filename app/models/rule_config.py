"""Schema for the draft N42-17 correlation rule file."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
EventField = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")]
PositiveInt = Annotated[int, Field(gt=0)]


class _ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RuleCount(_ConfigModel):
    mode: Literal["distinct", "state_changes"]
    field: EventField


class RuleAction(_ConfigModel):
    create_incident: bool
    incident_severity: NonEmptyText
    title: NonEmptyText


class CorrelationRule(_ConfigModel):
    rule_id: NonEmptyText
    name: NonEmptyText
    description: NonEmptyText | None = None
    enabled: bool = False
    window_seconds: PositiveInt
    threshold: PositiveInt
    group_by: list[EventField] = Field(min_length=1)
    match: dict[EventField, NonEmptyText] = Field(min_length=1)
    count: RuleCount | None = None
    action: RuleAction

    @field_validator("group_by")
    @classmethod
    def validate_group_fields(cls, fields: list[str]) -> list[str]:
        if len(fields) != len(set(fields)):
            raise ValueError("group_by fields must be unique")
        return fields


class RuleConfiguration(_ConfigModel):
    version: NonEmptyText
    rules: list[CorrelationRule] = Field(min_length=1)

    @field_validator("rules")
    @classmethod
    def validate_rule_ids(cls, rules: list[CorrelationRule]) -> list[CorrelationRule]:
        rule_ids = [rule.rule_id for rule in rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("rule_id values must be unique")
        return rules
