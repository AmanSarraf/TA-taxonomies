"""Public suite contract for TA-agents: models + Suite protocol.

Use case: import Node, ToolResult, Suite, etc. from here — the boundary
between TA-taxonomies and the agent runtime. Do not import suite loaders or
Neo4j helpers into agents.

Tool methods (see also ``protocols.Suite``)::

    search_nodes · get_neighbors · enumerate_paths · score_paths

Rules: suite-scoped ids; source + source_id on nodes; evidence is a pointer,
not a licensed payload.
"""

from ta_taxonomies.contract.models import (
    Candidate,
    Edge,
    Node,
    Path,
    PolicyRef,
    PruningStats,
    ScoredPath,
    SuiteName,
    ToolResult,
)
from ta_taxonomies.contract.protocols import Suite

__all__ = [
    "Candidate",
    "Edge",
    "Node",
    "Path",
    "PolicyRef",
    "PruningStats",
    "ScoredPath",
    "Suite",
    "SuiteName",
    "ToolResult",
]
