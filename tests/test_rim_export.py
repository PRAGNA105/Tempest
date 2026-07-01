from pathlib import Path

from graph import Edge, Node, RepositoryGraph
from rim import build_rim, export_rim_json
from scanners import URLFinding


def test_build_rim_maps_graph_and_findings():
    graph = RepositoryGraph(
        nodes=[Node(id="file:app.py", label="app.py", type="file", source_file="app.py")],
        edges=[],
    )
    finding = URLFinding(
        id="url-1",
        value="https://prod.example.com",
        source_file="file:app.py",
        url="https://prod.example.com",
        hostname="prod.example.com",
        confidence=0.8,
    )

    rim = build_rim(graph, [finding])

    assert {node.id for node in rim.nodes} == {"file:app.py", "finding:url-1"}
    assert rim.edges[0].source == "file:app.py"
    assert rim.edges[0].target == "finding:url-1"


def test_export_rim_json_writes_file(tmp_path):
    rim = build_rim(RepositoryGraph())
    output = export_rim_json(rim, Path(tmp_path) / "rim.json")

    assert output.exists()
    assert '"schema_version": "0.1"' in output.read_text(encoding="utf-8")

