from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from scanners.models import Finding


class Scanner(ABC):
    """Base interface for deterministic repository scanners."""

    name: str

    @abstractmethod
    def scan(self, repository_path: Path) -> list[Finding]:
        """Scan a repository path and return deterministic findings."""

