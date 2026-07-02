from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EnvironmentName(str, Enum):  # noqa: UP042 - Python 3.10 test runtime lacks StrEnum.
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"
    QA = "qa"


class EnvironmentCandidate(BaseModel):
    id: str
    name: EnvironmentName
    source_finding_id: str
    source_finding_type: str
    source_file: str
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: str
    metadata: dict[str, Any] = Field(default_factory=dict)
