import sys
from pathlib import Path

import pytest

from graphify_adapter import GraphifyCliError, GraphifyJsonAdapter, run_graphify_cli

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


def test_graphify_cli_wrapper_runs_command_and_validates_graph_json(tmp_path):
    script = _fake_graphify_script(tmp_path)
    graph_json = tmp_path / "repo" / "graphify-out" / "graph.json"
    repository = tmp_path / "repo"
    repository.mkdir()

    result = run_graphify_cli(
        repository,
        [sys.executable, str(script), "{graph_json}", "{repository}"],
        graph_json=graph_json,
    )

    assert result.returncode == 0
    assert result.graph_json == graph_json
    assert result.command[-2] == str(graph_json)
    assert result.command[-1] == str(repository.resolve())
    assert "wrote graph" in result.stdout
    assert graph_json.exists()


def test_graphify_cli_wrapper_reports_nonzero_exit(tmp_path):
    repository = tmp_path / "repo"
    repository.mkdir()
    script = tmp_path / "fail_graphify.py"
    script.write_text(
        "import sys\nsys.stderr.write('graphify failed')\nsys.exit(7)\n",
        encoding="utf-8",
    )

    with pytest.raises(GraphifyCliError, match="exit code 7"):
        run_graphify_cli(repository, [sys.executable, str(script)])


def _fake_graphify_script(tmp_path):
    script = tmp_path / "fake_graphify.py"
    script.write_text(
        "\n".join(
            [
                "import json",
                "import sys",
                "from pathlib import Path",
                "graph_json = Path(sys.argv[1])",
                "graph_json.parent.mkdir(parents=True, exist_ok=True)",
                "graph_json.write_text(json.dumps({",
                "    'directed': True,",
                "    'multigraph': True,",
                "    'graph': {},",
                "    'nodes': [{",
                "        'id': 'file:api.py',",
                "        'label': 'api.py',",
                "        'kind': 'file',",
                "        'source_file': 'api.py',",
                "    }],",
                "    'links': [],",
                "}), encoding='utf-8')",
                "print('wrote graph')",
            ]
        ),
        encoding="utf-8",
    )
    return script
