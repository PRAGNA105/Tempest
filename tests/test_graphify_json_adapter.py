from pathlib import Path

import pytest

from graphify_adapter import GraphifyJsonAdapter


FIXTURE = Path(__file__).parent / "fixtures" / "graphify_graph.json"


def test_graphify_json_adapter_loads_node_link_fixture():
    graph = GraphifyJsonAdapter(FIXTURE).build_graph(Path("."))

    assert graph.metadata["adapter"] == "graphify_json"
    assert graph.metadata["graphify_format"] == "networkx_node_link"
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2

    function_node = next(node for node in graph.nodes if node.id == "function:api.handle_request")
    assert function_node.label == "handle_request"
    assert function_node.type == "function"
    assert function_node.source_file == "api.py"
    assert function_node.metadata["file_type"] == "code"
    assert function_node.metadata["_origin"] == "ast"


def test_graphify_json_adapter_maps_confidence_tags():
    graph = GraphifyJsonAdapter(FIXTURE).load_graph_json(FIXTURE)

    defines_edge = next(edge for edge in graph.edges if edge.relation == "defines")
    calls_edge = next(edge for edge in graph.edges if edge.relation == "calls")

    assert defines_edge.confidence == 1.0
    assert calls_edge.confidence == 0.85
    assert calls_edge.metadata["graphify_confidence"] == "INFERRED"
    assert calls_edge.metadata["confidence_score"] == 0.85


def test_graphify_json_adapter_uses_repository_default_path(tmp_path):
    graphify_out = tmp_path / "graphify-out"
    graphify_out.mkdir()
    target = graphify_out / "graph.json"
    target.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    graph = GraphifyJsonAdapter().build_graph(tmp_path)

    assert graph.node_ids() == {
        "file:api.py",
        "function:api.handle_request",
        "function:storage.save_document",
    }


def test_graphify_json_adapter_reports_missing_graph(tmp_path):
    with pytest.raises(FileNotFoundError):
        GraphifyJsonAdapter().build_graph(tmp_path)

