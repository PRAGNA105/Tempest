from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from graphify_adapter.json_adapter import DEFAULT_GRAPHIFY_OUTPUT


class GraphifyCliError(RuntimeError):
    """Raised when the optional Graphify CLI invocation fails."""


@dataclass(frozen=True)
class GraphifyCliResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    graph_json: Path


def run_graphify_cli(
    repository_path: Path,
    command: list[str],
    *,
    graph_json: Path | None = None,
    timeout_seconds: float | None = None,
) -> GraphifyCliResult:
    repository = repository_path.resolve()
    if not repository.exists():
        raise FileNotFoundError(f"Repository path not found: {repository_path}")
    if not repository.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repository_path}")

    expected_graph_json = graph_json or repository / DEFAULT_GRAPHIFY_OUTPUT
    rendered_command = _render_command(command, repository, expected_graph_json)

    try:
        completed = subprocess.run(
            rendered_command,
            cwd=repository,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Graphify CLI command not found: {rendered_command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise GraphifyCliError(
            f"Graphify CLI command timed out after {timeout_seconds} seconds"
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        message = f"Graphify CLI command failed with exit code {completed.returncode}"
        if detail:
            message = f"{message}: {detail}"
        raise GraphifyCliError(message)

    if not expected_graph_json.exists():
        raise FileNotFoundError(
            f"Graphify CLI completed but graph JSON was not found: {expected_graph_json}"
        )

    return GraphifyCliResult(
        command=rendered_command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        graph_json=expected_graph_json,
    )


def _render_command(command: list[str], repository: Path, graph_json: Path) -> list[str]:
    if not command:
        raise ValueError("Graphify CLI command cannot be empty")

    output_dir = graph_json.parent
    replacements = {
        "repository": str(repository),
        "graph_json": str(graph_json),
        "graphify_output_dir": str(output_dir),
    }
    rendered = [arg.format(**replacements) for arg in command]
    if any(not arg for arg in rendered):
        raise ValueError("Graphify CLI command arguments cannot be empty")
    return rendered
