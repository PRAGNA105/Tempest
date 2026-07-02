from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnnotationType(str, Enum):  # noqa: UP042 - Python 3.10 test runtime lacks StrEnum.
    ENVIRONMENT = "environment"
    PRODUCTION_BOUNDARY = "production_boundary"


class AnnotatedNode(BaseModel):
    id: str
    target_node_id: str
    annotation_type: AnnotationType
    source_candidate_id: str
    source_finding_id: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
