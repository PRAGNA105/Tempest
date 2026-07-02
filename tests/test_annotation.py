from annotation import AnnotatedNode, AnnotationType, annotate_rim
from boundary import ProductionBoundaryCandidate, ProductionBoundaryType
from environment import EnvironmentCandidate, EnvironmentName
from graph import Node, RepositoryGraph
from rim import build_rim
from rim.models import RIMEdgeType, RIMNodeKind
from scanners import URLFinding


def _url_finding():
    return URLFinding(
        id="url-1",
        value="https://api.prod.example.com",
        source_file="api.py",
        line=10,
        column=14,
        confidence=0.95,
        evidence="https://api.prod.example.com",
        url="https://api.prod.example.com",
        hostname="api.prod.example.com",
        environment_hint="production",
        metadata={"scanner": "url_scanner"},
    )


def _environment_candidate(finding):
    return EnvironmentCandidate(
        id="environment-1",
        name=EnvironmentName.PRODUCTION,
        source_finding_id=finding.id,
        source_finding_type=finding.__class__.__name__,
        source_file=finding.source_file,
        line=finding.line,
        column=finding.column,
        confidence=0.902,
        evidence=finding.evidence or finding.value,
        metadata={"discovery": "environment_discovery"},
    )


def _boundary_candidate(finding, environment):
    return ProductionBoundaryCandidate(
        id="boundary-1",
        boundary_type=ProductionBoundaryType.EXTERNAL_URL,
        source_environment_id=environment.id,
        source_finding_id=finding.id,
        source_finding_type=finding.__class__.__name__,
        source_file=finding.source_file,
        line=finding.line,
        column=finding.column,
        externally_reachable=True,
        confidence=0.857,
        evidence=finding.evidence or finding.value,
        metadata={"discovery": "production_boundary_discovery"},
    )


def test_annotation_contract_accepts_annotated_node():
    annotation = AnnotatedNode(
        id="annotation-1",
        target_node_id="file:api.py",
        annotation_type=AnnotationType.ENVIRONMENT,
        source_candidate_id="environment-1",
        source_finding_id="url-1",
        confidence=0.9,
    )

    assert annotation.annotation_type == AnnotationType.ENVIRONMENT
    assert annotation.target_node_id == "file:api.py"


def test_annotate_rim_adds_environment_node_edge_and_metadata_to_source_file():
    finding = _url_finding()
    graph = RepositoryGraph(
        nodes=[Node(id="file:api.py", label="api.py", type="file", source_file="api.py")]
    )
    rim = build_rim(graph, [finding])
    environment = _environment_candidate(finding)

    annotated = annotate_rim(rim, [environment])

    environment_node = next(
        node for node in annotated.nodes if node.id == "environment:environment-1"
    )
    file_node = next(node for node in annotated.nodes if node.id == "file:api.py")
    edge = next(
        edge
        for edge in annotated.edges
        if edge.type == RIMEdgeType.BELONGS_TO_ENVIRONMENT
    )

    assert environment_node.kind == RIMNodeKind.ENVIRONMENT
    assert environment_node.metadata["candidate"]["source_finding_id"] == "url-1"
    assert edge.source == "file:api.py"
    assert edge.target == "environment:environment-1"
    assert file_node.metadata["annotations"][0]["annotation_type"] == "environment"
    assert rim.metadata.get("annotation") is None


def test_annotate_rim_adds_boundary_node_edge_and_metadata_to_source_file():
    finding = _url_finding()
    graph = RepositoryGraph(
        nodes=[Node(id="file:api.py", label="api.py", type="file", source_file="api.py")]
    )
    rim = build_rim(graph, [finding])
    environment = _environment_candidate(finding)
    boundary = _boundary_candidate(finding, environment)

    annotated = annotate_rim(rim, [environment], [boundary])

    boundary_node = next(node for node in annotated.nodes if node.id == "boundary:boundary-1")
    file_node = next(node for node in annotated.nodes if node.id == "file:api.py")
    edge = next(edge for edge in annotated.edges if edge.type == RIMEdgeType.CROSSES_BOUNDARY)

    assert boundary_node.kind == RIMNodeKind.PRODUCTION_BOUNDARY
    assert boundary_node.metadata["candidate"]["externally_reachable"] is True
    assert edge.source == "file:api.py"
    assert edge.target == "boundary:boundary-1"
    assert file_node.metadata["annotations"][1]["annotation_type"] == "production_boundary"


def test_annotate_rim_falls_back_to_finding_node_when_source_file_node_is_absent():
    finding = _url_finding()
    rim = build_rim(RepositoryGraph(), [finding])
    environment = _environment_candidate(finding)

    annotated = annotate_rim(rim, [environment])

    edge = next(
        edge
        for edge in annotated.edges
        if edge.type == RIMEdgeType.BELONGS_TO_ENVIRONMENT
    )
    finding_node = next(node for node in annotated.nodes if node.id == "finding:url-1")

    assert edge.source == "finding:url-1"
    assert finding_node.metadata["annotations"][0]["source_finding_id"] == "url-1"


def test_annotate_rim_is_idempotent_for_existing_annotation_edges():
    finding = _url_finding()
    graph = RepositoryGraph(
        nodes=[Node(id="file:api.py", label="api.py", type="file", source_file="api.py")]
    )
    rim = build_rim(graph, [finding])
    environment = _environment_candidate(finding)

    once = annotate_rim(rim, [environment])
    twice = annotate_rim(once, [environment])
    environment_edges = [
        edge for edge in twice.edges if edge.type == RIMEdgeType.BELONGS_TO_ENVIRONMENT
    ]
    environment_nodes = [node for node in twice.nodes if node.id == "environment:environment-1"]

    assert len(environment_edges) == 1
    assert len(environment_nodes) == 1
