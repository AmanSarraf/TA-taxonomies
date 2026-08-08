"""Suite protocol — the tool surface every taxonomy suite must implement.

Use case: a shared structural contract (search_nodes, get_neighbors,
enumerate_paths, score_paths) so ESCO, O*NET, SFIA, and BLS expose the
same capabilities with suite-specific internals.

Why it exists: TA-agents can call suites interchangeably by name without
importing loaders or Neo4j details. This file is the interface; each suite
package provides the implementation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ta_taxonomies.contract.models import ToolResult


@runtime_checkable
class Suite(Protocol):
    """Typed tool surface shared by all taxonomy suites (Locate/Connect/Pathfind)."""

    name: str

    def search_nodes(self, text: str, kind: str | None = None) -> ToolResult:
        """Locate: resolve free text to node candidates with confidence."""
        ...

    def get_neighbors(
        self,
        node_id: str,
        rel_types: list[str] | None = None,
    ) -> ToolResult:
        """Connect: single-hop neighbors over suite-declared traversable rels."""
        ...

    def enumerate_paths(
        self,
        from_id: str,
        to_id: str,
        *,
        max_depth: int = 4,
        max_paths: int = 20,
    ) -> ToolResult:
        """Pathfind: depth-capped, cycle-free multi-hop paths between two nodes."""
        ...

    def score_paths(self, paths: list[list[str]], policy: str) -> ToolResult:
        """Evaluate: rank paths under a named, versioned policy (not free invent)."""
        ...
