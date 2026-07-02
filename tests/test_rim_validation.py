from graph import Node, RepositoryGraph
from rilde_cli.main import main
from rim import (
    RepositoryIntelligenceModel,
    RepositoryNode,
    RIMEdge,
    build_rim,
    export_rim_json,
    validate_rim,
    validate_rim_json,
)
from rim.models import RIMNodeKind
from scanners import URLFinding


def test_validate_rim_accepts_exported_rim_with_source_file_endpoint_warning():
    rim = _rim_with_source_file_edge()

    result = validate_rim(rim)

    assert result.valid is True
    assert result.error_count == 0
    assert result.warning_count == 1
    assert result.issues[0].code == "edge_endpoint_uses_source_file"


def test_validate_rim_reports_duplicate_node_ids():
    rim = RepositoryIntelligenceModel(
        nodes=[
            RepositoryNode(id="node-1", label="node", kind=RIMNodeKind.FILE),
            RepositoryNode(id="node-1", label="duplicate", kind=RIMNodeKind.FILE),
        ]
    )

    result = validate_rim(rim)

    assert result.valid is False
    assert result.error_count == 1
    assert result.issues[0].code == "duplicate_node_id"


def test_validate_rim_reports_missing_edge_endpoint():
    rim = RepositoryIntelligenceModel(
        nodes=[RepositoryNode(id="node-1", label="node", kind=RIMNodeKind.FILE)],
        edges=[RIMEdge(source="node-1", target="missing-node", type="references")],
    )

    result = validate_rim(rim)

    assert result.valid is False
    assert result.issues[0].code == "missing_edge_endpoint"


def test_validate_rim_reports_duplicate_edges():
    edge = RIMEdge(source="node-1", target="node-2", type="references")
    rim = RepositoryIntelligenceModel(
        nodes=[
            RepositoryNode(id="node-1", label="source", kind=RIMNodeKind.FILE),
            RepositoryNode(id="node-2", label="target", kind=RIMNodeKind.FILE),
        ],
        edges=[edge, edge],
    )

    result = validate_rim(rim)

    assert result.valid is False
    assert result.issues[0].code == "duplicate_edge"


def test_validate_rim_json_reports_schema_validation_errors(tmp_path):
    path = tmp_path / "rim.json"
    path.write_text('{"nodes": [{"id": "node-1"}]}', encoding="utf-8")

    result = validate_rim_json(path)

    assert result.valid is False
    assert result.issues[0].code == "schema_validation_failed"


def test_cli_validate_rim_reports_success(tmp_path, capsys):
    rim_path = export_rim_json(_rim_with_source_file_edge(), tmp_path / "rim.json")

    exit_code = main(["validate-rim", str(rim_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "RIM validation passed." in captured.out
    assert "Warnings: 1" in captured.out


def test_cli_validate_rim_reports_failure(tmp_path, capsys):
    rim = RepositoryIntelligenceModel(
        nodes=[RepositoryNode(id="node-1", label="node", kind=RIMNodeKind.FILE)],
        edges=[RIMEdge(source="node-1", target="missing-node", type="references")],
    )
    rim_path = export_rim_json(rim, tmp_path / "rim.json")

    exit_code = main(["validate-rim", str(rim_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "RIM validation failed." in captured.out
    assert "missing_edge_endpoint" in captured.out


def _rim_with_source_file_edge():
    graph = RepositoryGraph(
        nodes=[Node(id="file:api.py", label="api.py", type="file", source_file="api.py")]
    )
    finding = URLFinding(
        id="url-1",
        value="https://api.prod.example.com",
        source_file="api.py",
        url="https://api.prod.example.com",
        hostname="api.prod.example.com",
        confidence=0.95,
    )
    return build_rim(graph, [finding])
