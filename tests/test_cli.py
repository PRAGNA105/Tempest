import json

from rilde_cli.main import main
from rilde_cli.pipeline import run_deterministic_pipeline


def test_run_deterministic_pipeline_writes_all_stage_artifacts(tmp_path):
    repository = _repository(tmp_path)
    graph_json = _graph_json(repository)
    output_dir = tmp_path / "state"

    result = run_deterministic_pipeline(
        repository,
        graph_json=graph_json,
        output_dir=output_dir,
    )

    assert result.counts["url_findings"] == 1
    assert result.counts["secret_findings"] == 1
    assert result.counts["environment_candidates"] == 1
    assert result.counts["boundary_candidates"] == 1
    assert result.counts["leak_findings"] == 1

    for path in result.paths.values():
        assert path.exists()

    report = json.loads(result.paths["report_json"].read_text(encoding="utf-8"))
    assert report["summary"]["total_findings"] == 1
    assert result.paths["report_markdown"].read_text(encoding="utf-8").startswith(
        "# RILDE Security Report"
    )


def test_cli_run_command_prints_summary(tmp_path, capsys):
    repository = _repository(tmp_path)
    graph_json = _graph_json(repository)
    output_dir = tmp_path / "state"

    exit_code = main(
        [
            "run",
            str(repository),
            "--graph-json",
            str(graph_json),
            "--output-dir",
            str(output_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "RILDE deterministic pipeline complete." in captured.out
    assert "Leak findings: 1" in captured.out
    assert (output_dir / "reports" / "report.md").exists()


def test_cli_run_command_returns_error_for_missing_graph(tmp_path, capsys):
    repository = _repository(tmp_path)

    exit_code = main(["run", str(repository), "--output-dir", str(tmp_path / "state")])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Graphify graph JSON not found" in captured.err


def _repository(tmp_path):
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "api.py").write_text(
        "\n".join(
            [
                'API_TOKEN = "abc123XYZ789secret"',
                'PROD_URL = "https://api.prod.example.com"',
            ]
        ),
        encoding="utf-8",
    )
    return repository


def _graph_json(repository):
    graph_dir = repository / "graphify-out"
    graph_dir.mkdir()
    graph_json = graph_dir / "graph.json"
    graph_json.write_text(
        json.dumps(
            {
                "directed": True,
                "multigraph": True,
                "graph": {},
                "nodes": [
                    {
                        "id": "file:api.py",
                        "label": "api.py",
                        "kind": "file",
                        "source_file": "api.py",
                    }
                ],
                "links": [],
            }
        ),
        encoding="utf-8",
    )
    return graph_json
