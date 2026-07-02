from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LeakSeverity(str, Enum):  # noqa: UP042 - Python 3.10 test runtime lacks StrEnum.
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LeakFinding(BaseModel):
    id: str
    policy_id: str
    title: str
    severity: LeakSeverity
    source_node_id: str
    source_file: str | None = None
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: str
    related_node_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DetectionResult(BaseModel):
    policy_id: str
    findings: list[LeakFinding] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
