from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "graphify-out",
        "state",
    }
)

DEFAULT_TEXT_EXTENSIONS = frozenset(
    {
        ".cfg",
        ".conf",
        ".css",
        ".env",
        ".go",
        ".html",
        ".ini",
        ".java",
        ".js",
        ".json",
        ".jsx",
        ".kt",
        ".md",
        ".pem",
        ".php",
        ".properties",
        ".py",
        ".rb",
        ".rs",
        ".sh",
        ".sql",
        ".toml",
        ".tf",
        ".tfvars",
        ".ts",
        ".tsx",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
)


@dataclass(frozen=True)
class TraversalRules:
    excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS
    text_extensions: frozenset[str] = DEFAULT_TEXT_EXTENSIONS
    max_file_bytes: int = 1_000_000
    include_extensionless: bool = True


@dataclass(frozen=True)
class SourceFile:
    path: Path
    relative_path: str
    text: str
    encoding: str = "utf-8"
    metadata: dict[str, object] = field(default_factory=dict)


def iter_source_files(repository_path: Path, rules: TraversalRules | None = None) -> Iterator[SourceFile]:
    active_rules = rules or TraversalRules()
    root = repository_path.resolve()

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _is_excluded(path, root, active_rules):
            continue
        if not _is_text_candidate(path, active_rules):
            continue
        if path.stat().st_size > active_rules.max_file_bytes:
            continue

        text = _read_text(path)
        if text is None:
            continue

        yield SourceFile(
            path=path,
            relative_path=path.relative_to(root).as_posix(),
            text=text,
            metadata={"size_bytes": path.stat().st_size},
        )


def _is_excluded(path: Path, root: Path, rules: TraversalRules) -> bool:
    relative_parts = path.relative_to(root).parts
    return any(part in rules.excluded_dirs for part in relative_parts[:-1])


def _is_text_candidate(path: Path, rules: TraversalRules) -> bool:
    suffix = path.suffix.lower()
    if suffix in rules.text_extensions:
        return True
    return rules.include_extensionless and suffix == ""


def _read_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None

    if b"\x00" in raw:
        return None

    for encoding in ("utf-8", "utf-8-sig"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    return None
