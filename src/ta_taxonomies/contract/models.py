"""Shared Pydantic models for the suite contract (typed tool I/O).

Use case: define the only data shapes TA-agents (and other callers) should
depend on when talking to any suite — Node, Edge, Candidate, ToolResult.

Why it exists: keeps Locate/Connect/Pathfind results structured (ids,
confidence, warnings, evidence pointers) instead of free-form prose or
Neo4j-specific types. Suites fill these models; agents consume them.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SuiteName = Literal["esco", "onet", "sfia", "bls"]


class Node(BaseModel):
    """A graph node returned by suite tools."""

    id: str = Field(..., description="Suite-scoped id, e.g. esco:occupation:…")
    kind: str = Field(..., description="Canonical or suite kind: Occupation, Skill, …")
    label: str
    source: str
    source_id: str = Field(..., description="Native source identifier (usually URI)")
    properties: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """A graph edge returned by suite tools."""

    type: str
    from_id: str
    to_id: str
    properties: dict[str, Any] = Field(default_factory=dict)


class Candidate(BaseModel):
    """A Locate / search_nodes hit."""

    node: Node
    confidence: float = Field(..., ge=0.0, le=1.0)
    method: str = Field(..., description="exact_pref | exact_alt | contains | …")


class ToolResult(BaseModel):
    """Typed envelope for suite tool responses."""

    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)
    paths: list[list[str]] = Field(
        default_factory=list,
        description="Node-id sequences for enumerate_paths",
    )
    warnings: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(
        default_factory=list,
        description="Pointers / citations (not licensed payloads)",
    )
    meta: dict[str, Any] = Field(default_factory=dict)
