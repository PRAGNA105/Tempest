from __future__ import annotations

from pydantic import BaseModel, Field

from detection.models import LeakSeverity


class ReportSummary(BaseModel):
    total_findings: int = Field(default=0, ge=0)
    critical: int = Field(default=0, ge=0)
    high: int = Field(default=0, ge=0)
    medium: int = Field(default=0, ge=0)
    low: int = Field(default=0, ge=0)


class ReportFinding(BaseModel):
    evidence_id: str
    leak_finding_id: str
    policy_id: str
    title: str
    severity: LeakSeverity
    source_file: str | None = None
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    summary: str
    primary_node_id: str | None = None
    related_node_ids: list[str] = Field(default_factory=list)
    fact_count: int = Field(default=0, ge=0)


class SecurityReport(BaseModel):
    schema_version: str = "0.1"
    title: str = "RILDE Security Report"
    summary: ReportSummary = Field(default_factory=ReportSummary)
    findings: list[ReportFinding] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
