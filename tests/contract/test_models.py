"""Public contract model tests."""

from typing import get_type_hints

from pydantic import TypeAdapter

from ta_taxonomies.contract import Edge, Path, PolicyRef, Suite, SuiteName, ToolResult


def test_jobtech_is_a_supported_suite_name() -> None:
    """The adopted fifth suite must be representable by the shared contract."""
    adapter = TypeAdapter(SuiteName)

    assert adapter.validate_python("jobtech") == "jobtech"


def test_path_result_preserves_ordered_nodes_and_edges() -> None:
    """Pathfinder results must explain which relationship joins each node."""
    path = Path(
        nodes=["esco:occupation:developer", "esco:skill:python"],
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

    assert result.paths[0].nodes == ["esco:occupation:developer", "esco:skill:python"]
    assert result.paths[0].edges[0].type == "HAS_SKILL"


def test_score_paths_requires_a_named_versioned_policy() -> None:
    """Evaluator policy identity must survive calls and result metadata."""
    policy = PolicyRef(name="esco-binary", version="1")

    hints = get_type_hints(Suite.score_paths)

    assert policy.model_dump() == {"name": "esco-binary", "version": "1"}
    assert hints["policy"] is PolicyRef
