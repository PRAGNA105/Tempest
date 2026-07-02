from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProductionBoundaryType(str, Enum):  # noqa: UP042 - Python 3.10 test runtime lacks StrEnum.
    EXTERNAL_URL = "external_url"
    EXTERNAL_DATABASE = "external_database"
    CLOUD_RESOURCE = "cloud_resource"


class ProductionBoundaryCandidate(BaseModel):
    id: str
    boundary_type: ProductionBoundaryType
    source_environment_id: str
    source_finding_id: str
    source_finding_type: str
    source_file: str
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    externally_reachable: bool
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: str
    metadata: dict[str, Any] = Field(default_factory=dict)
