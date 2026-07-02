from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from detection.models import LeakSeverity


class EvidenceNode(BaseModel):
    id: str
    label: str
    kind: str
    source_file: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceFact(BaseModel):
    key: str
    value: Any
    source_node_id: str | None = None


class EvidenceRecord(BaseModel):
    id: str
    leak_finding_id: str
    policy_id: str
    title: str
    severity: LeakSeverity
    summary: str
    source_file: str | None = None
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    primary_node: EvidenceNode | None = None
    related_nodes: list[EvidenceNode] = Field(default_factory=list)
    facts: list[EvidenceFact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
