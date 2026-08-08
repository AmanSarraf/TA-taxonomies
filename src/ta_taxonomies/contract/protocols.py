"""Suite protocol — every suite implements this surface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ta_taxonomies.contract.models import ToolResult


@runtime_checkable
class Suite(Protocol):
    """Typed tool surface shared by all taxonomy suites."""

    name: str

    def search_nodes(self, text: str, kind: str | None = None) -> ToolResult:
        """Resolve free text to node candidates with confidence."""
        ...

    def get_neighbors(
        self,
        node_id: str,
        rel_types: list[str] | None = None,
    ) -> ToolResult:
        """Single-hop neighbors over traversable relationship types."""
        ...

    def enumerate_paths(
        self,
        from_id: str,
        to_id: str,
        *,
        max_depth: int = 4,
        max_paths: int = 20,
    ) -> ToolResult:
        """Depth-capped, cycle-free multi-hop paths."""
        ...

    def score_paths(self, paths: list[list[str]], policy: str) -> ToolResult:
        """Rank paths under a named, versioned policy."""
        ...
