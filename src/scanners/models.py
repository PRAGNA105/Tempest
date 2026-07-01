from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class Finding(BaseModel):
    id: str
    value: str
    source_file: str
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SecretFinding(Finding):
    secret_type: str
    entropy: float | None = Field(default=None, ge=0.0)


class URLFinding(Finding):
    url: str
    scheme: str | None = None
    hostname: str | None = None
    environment_hint: str | None = None


class DatabaseFinding(Finding):
    database_type: str
    host: str | None = None
    database_name: str | None = None
    environment_hint: str | None = None


class CloudResourceFinding(Finding):
    provider: CloudProvider
    resource_type: str
    resource_id: str
    region: str | None = None
