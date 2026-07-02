from __future__ import annotations

from typing import Protocol

from detection.models import LeakFinding
from rim.models import RepositoryIntelligenceModel


class DetectionPolicy(Protocol):
    id: str
    name: str

    def detect(self, rim: RepositoryIntelligenceModel) -> list[LeakFinding]:
        """Return deterministic leak findings from a RIM."""
