from graph import Edge, Node, RepositoryGraph
from graphify_adapter import StubGraphifyAdapter
from scanners import CloudProvider, CloudResourceFinding, SecretFinding


def test_repository_graph_contract_accepts_nodes_and_edges():
    graph = RepositoryGraph(
        nodes=[
            Node(id="file:app.py", label="app.py", type="file", source_file="app.py"),
            Node(id="fn:main", label="main", type="function", source_file="app.py"),
        ],
        edges=[Edge(source="file:app.py", target="fn:main", relation="defines")],
    )

    assert graph.node_ids() == {"file:app.py", "fn:main"}


def test_scanner_contracts_cover_secret_and_cloud_findings():
    secret = SecretFinding(
        id="secret-1",
        value="redacted",
        source_file="settings.py",
        secret_type="api_key",
        confidence=0.9,
    )
    cloud = CloudResourceFinding(
        id="aws-1",
        value="arn:aws:s3:::prod-bucket",
        source_file="settings.py",
        provider=CloudProvider.AWS,
        resource_type="s3_bucket",
        resource_id="prod-bucket",
    )

    assert secret.secret_type == "api_key"
    assert cloud.provider == CloudProvider.AWS


def test_stub_graphify_adapter_returns_repository_graph(tmp_path):
    graph = StubGraphifyAdapter().build_graph(tmp_path)

    assert graph.metadata["adapter"] == "stub_graphify"
    assert graph.nodes[0].type == "repository"

