"""Public contract model tests."""

import pytest
from pydantic import TypeAdapter, ValidationError

from ta_taxonomies.contract import (
    Edge,
    Node,
    Path,
    PolicyRef,
    PruningStats,
    ScoredPath,
    Suite,
    SuiteName,
    ToolResult,
)


def test_jobtech_is_a_supported_suite_name() -> None:
    """The adopted fifth suite must be representable by the shared contract."""
    adapter = TypeAdapter(SuiteName)

    assert adapter.validate_python("jobtech") == "jobtech"


def test_node_rejects_unknown_source() -> None:
    """Taxonomy facts must identify one of the declared suites as their source."""
    with pytest.raises(ValidationError, match="Input should be"):
        Node(
            id="linkedin:1", kind="Occupation", label="developer", source="linkedin", source_id="1"
        )


def test_path_result_preserves_ordered_nodes_and_edges() -> None:
    """Pathfinder results must explain which relationship joins each node."""
    path = Path(
        node_ids=["esco:occupation:developer", "esco:skill:python"],
        edges=[
            Edge(
                type="HAS_SKILL",
                from_id="esco:occupation:developer",
                to_id="esco:skill:python",
                properties={"relation_type": "essential"},
            )
        ],
    )

    result = ToolResult(paths=[path])

    assert result.paths[0].node_ids == ["esco:occupation:developer", "esco:skill:python"]
    assert result.paths[0].edges[0].type == "HAS_SKILL"


def test_path_rejects_wrong_edge_count() -> None:
    """A route with n nodes must contain exactly n - 1 edges."""
    with pytest.raises(ValidationError, match="exactly 2 edges"):
        Path(node_ids=["a", "b", "c"], edges=[])


def test_path_rejects_non_adjacent_edge() -> None:
    """Every edge must connect its adjacent node IDs in route order."""
    with pytest.raises(ValidationError, match="edge 0 must connect 'a' to 'b'"):
        Path(
            node_ids=["a", "b"],
            edges=[Edge(type="RELATED_TO", from_id="a", to_id="c")],
        )


def test_path_accepts_reverse_oriented_adjacent_edge() -> None:
    """Undirected traversal may cross an edge opposite its stored direction."""
    path = Path(
        node_ids=["a", "b"],
        edges=[Edge(type="RELATED_TO", from_id="b", to_id="a")],
    )

    assert path.edges[0].from_id == "b"


def test_single_node_path_accepts_no_edges() -> None:
    path = Path(node_ids=["a"], edges=[])

    assert path.node_ids == ["a"]


def test_scored_path_carries_score_and_policy() -> None:
    """A ranking result must identify both its score and the policy used."""
    policy = PolicyRef(name="esco-binary", version="1")
    scored = ScoredPath(
        path=Path(node_ids=["a", "b"], edges=[Edge(type="RELATED_TO", from_id="a", to_id="b")]),
        score=0.75,
        policy=policy,
    )

    result = ToolResult(scored_paths=[scored])

    assert result.scored_paths[0].score == 0.75
    assert result.scored_paths[0].policy == policy


def test_pruning_stats_are_typed_and_consistent() -> None:
    """Path enumeration reports counts of cut routes, never their payloads."""
    pruning = PruningStats(considered=12, returned=5, pruned=7)

    result = ToolResult(pruning=pruning)

    assert result.pruning == pruning


def test_pruning_stats_reject_inconsistent_counts() -> None:
    with pytest.raises(ValidationError, match="considered must equal returned plus pruned"):
        PruningStats(considered=12, returned=5, pruned=6)


def test_conforming_suite_is_runtime_checkable() -> None:
    """The protocol supports instance checks for registries and tests."""

    class ExampleSuite:
        name: SuiteName = "esco"

        def search_nodes(self, text: str, kind: str | None = None) -> ToolResult:
            return ToolResult()

        def get_neighbors(
            self,
            node_id: str,
            rel_types: list[str] | None = None,
        ) -> ToolResult:
            return ToolResult()

        def enumerate_paths(
            self,
            from_id: str,
            to_id: str,
            *,
            max_depth: int = 4,
            max_paths: int = 20,
        ) -> ToolResult:
            return ToolResult()

        def score_paths(self, paths: list[Path], policy: PolicyRef) -> ToolResult:
            return ToolResult()

    assert isinstance(ExampleSuite(), Suite)


def test_suite_protocol_does_not_support_issubclass() -> None:
    """The protocol has a data member, so only instance checks are supported."""

    class ExampleSuite:
        name: SuiteName = "esco"

    with pytest.raises(TypeError, match="Protocols with non-method members"):
        issubclass(ExampleSuite, Suite)
