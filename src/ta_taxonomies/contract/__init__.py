"""Suite contract package — public types and protocol for all taxonomies.

Use case: the boundary between TA-taxonomies and TA-agents. Agents should
import from here (models + Suite protocol), not from suite loaders or Neo4j
helpers.

Tool surface every suite implements::

    search_nodes(text, kind?)                -> candidates + confidence
    get_neighbors(node_id, rel_types?)       -> nodes + edges
    enumerate_paths(from_id, to_id, limits)  -> depth-capped, cycle-free paths
    score_paths(paths, policy)               -> ranked under a named policy

Rules: suite-scoped ids; source + source_id on nodes; evidence is a pointer,
not a licensed payload.
"""

from ta_taxonomies.contract.models import (
    Candidate,
    Edge,
    Node,
    ToolResult,
)
from ta_taxonomies.contract.protocols import Suite

__all__ = [
    "Candidate",
    "Edge",
    "Node",
    "Suite",
    "ToolResult",
]
