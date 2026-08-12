"""ESCO suite tools: query the loaded graph via the shared suite contract.

Use case: after load.py has populated Neo4j, callers (tests, CLIs, later
TA-agents) use ``EscoSuite`` for Locate/Connect/Pathfind-style operations —
``search_nodes``, ``get_neighbors``, ``enumerate_paths``. Returns contract
``ToolResult`` models, not raw Neo4j records.

Why it exists: keep Cypher and confidence policy in a library so agents do
not reimplement graph access. LangGraph ``@tool`` wiring stays in TA-agents.
``score_paths`` is a deliberate stub until a named TA scoring policy exists
(ESCO occ–skill links are essential/optional only, not numeric weights).
"""

from __future__ import annotations

from typing import Any

from neo4j import Driver, Session

from ta_taxonomies.contract.models import (
    Candidate,
    Edge,
    Node,
    Path,
    PolicyRef,
    PruningStats,
    ToolResult,
)
from ta_taxonomies.suites.esco.config import (
    CONF_CASEFOLD_AMBIGUOUS,
    CONF_CASEFOLD_UNIQUE,
    CONF_CONTAINS,
    CONF_EXACT_ALT,
    CONF_EXACT_PREF,
    KIND_ALIASES,
    LABEL_ESCO_NODE,
    LABEL_ISCO_GROUP,
    LABEL_OCCUPATION,
    LABEL_SKILL_GROUP,
    MAX_BRANCHING,
    MAX_FRONTIER_PATHS,
    MAX_PATH_DEPTH,
    MAX_PATHS,
    REL_BROADER_THAN,
    REL_CLASSIFIED_UNDER,
    REL_HAS_SKILL,
    SOURCE,
    TRAVERSABLE_RELS,
)


def _record_to_node(rec: dict[str, Any]) -> Node:
    labels = list(rec.get("labels") or [])
    kind = rec.get("kind") or (labels[0] if labels else "Node")
    return Node(
        id=rec["id"],
        kind=str(kind),
        label=rec.get("pref_label") or "",
        source="esco",
        source_id=rec.get("source_id") or rec.get("uri") or rec["id"],
        properties={
            k: v
            for k, v in rec.items()
            if k
            not in {
                "id",
                "pref_label",
                "source",
                "source_id",
                "labels",
                "kind",
            }
            and v is not None
        },
    )


def _fetch_by_ids(session: Session, ids: list[str]) -> dict[str, Node]:
    if not ids:
        return {}
    result = session.run(
        f"""
        MATCH (n:{LABEL_ESCO_NODE})
        WHERE n.source = $source AND n.id IN $ids
        RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
               n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
               n.code AS code, n.description AS description,
               n.alt_labels AS alt_labels, n.skill_type AS skill_type,
               n.reuse_level AS reuse_level, n.isco_group AS isco_group,
               labels(n) AS labels
        """,
        ids=ids,
        source=SOURCE,
    )
    out: dict[str, Node] = {}
    for rec in result:
        node = _record_to_node(dict(rec))
        out[node.id] = node
    return out


class EscoSuite:
    """ESCO implementation of the suite contract (read path against Neo4j).

    Construct with a neo4j ``Driver`` from ``db.neo4j_driver`` (Docker or Aura).
    Call after the graph has been loaded; does not ingest xlsx/fixture data.
    """

    name = SOURCE

    def __init__(self, driver: Driver, database: str | None = None) -> None:
        self._driver = driver
        self._database = database

    def _session(self) -> Session:
        return self._driver.session(database=self._database)

    def search_nodes(self, text: str, kind: str | None = None) -> ToolResult:
        """Locate: resolve free text to ESCO nodes with confidence.

        Order: exact preferred label → exact alt label → case-insensitive
        preferred → substring on pref/alts. Never invents hits (``not_found``).
        ``kind`` optionally restricts labels (see ``KIND_ALIASES`` in config).
        """
        q = (text or "").strip()
        if not q:
            return ToolResult(warnings=["empty_query"])

        labels = [
            LABEL_OCCUPATION,
            LABEL_SKILL,
            LABEL_ISCO_GROUP,
            LABEL_SKILL_GROUP,
        ]
        if kind:
            normalized_kind = kind.lower().replace(" ", "_")
            mapped = KIND_ALIASES.get(normalized_kind)
            if mapped is None:
                return ToolResult(warnings=[f"unknown_kind:{kind}"])
            labels = [mapped]

        with self._session() as session:
            # 1) exact preferredLabel (case-sensitive)
            exact_pref = self._query_match(
                session,
                labels,
                """
                MATCH (n:EscoNode)
                WHERE n.source = $source
                  AND any(l IN labels(n) WHERE l IN $labels)
                  AND n.pref_label = $q
                RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
                       n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
                       n.code AS code, n.description AS description,
                       n.alt_labels AS alt_labels, labels(n) AS labels
                ORDER BY size(n.pref_label), n.id
                LIMIT 25
                """,
                {"labels": labels, "q": q, "source": SOURCE},
            )
            if exact_pref:
                cands = [
                    Candidate(
                        node=_record_to_node(r),
                        confidence=CONF_EXACT_PREF,
                        method="exact_pref",
                    )
                    for r in exact_pref
                ]
                return ToolResult(
                    candidates=cands,
                    nodes=[c.node for c in cands],
                    evidence=[f"esco:search:exact_pref:{q}"],
                )

            # 2) exact alt_label (list membership)
            exact_alt = self._query_match(
                session,
                labels,
                """
                MATCH (n:EscoNode)
                WHERE n.source = $source
                  AND any(l IN labels(n) WHERE l IN $labels)
                  AND n.alt_labels IS NOT NULL
                  AND $q IN n.alt_labels
                RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
                       n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
                       n.code AS code, n.description AS description,
                       n.alt_labels AS alt_labels, labels(n) AS labels
                ORDER BY size(n.pref_label), n.id
                LIMIT 25
                """,
                {"labels": labels, "q": q, "source": SOURCE},
            )
            if exact_alt:
                cands = [
                    Candidate(
                        node=_record_to_node(r),
                        confidence=CONF_EXACT_ALT,
                        method="exact_alt",
                    )
                    for r in exact_alt
                ]
                return ToolResult(
                    candidates=cands,
                    nodes=[c.node for c in cands],
                    evidence=[f"esco:search:exact_alt:{q}"],
                )

            # 3) case-insensitive unique pref match
            casefold = self._query_match(
                session,
                labels,
                """
                MATCH (n:EscoNode)
                WHERE n.source = $source
                  AND any(l IN labels(n) WHERE l IN $labels)
                  AND toLower(n.pref_label) = toLower($q)
                RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
                       n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
                       n.code AS code, n.description AS description,
                       n.alt_labels AS alt_labels, labels(n) AS labels
                ORDER BY size(n.pref_label), n.id
                LIMIT 25
                """,
                {"labels": labels, "q": q, "source": SOURCE},
            )
            if len(casefold) == 1:
                cands = [
                    Candidate(
                        node=_record_to_node(casefold[0]),
                        confidence=CONF_CASEFOLD_UNIQUE,
                        method="casefold_pref",
                    )
                ]
                return ToolResult(
                    candidates=cands,
                    nodes=[c.node for c in cands],
                    evidence=[f"esco:search:casefold_pref:{q}"],
                )
            if len(casefold) > 1:
                cands = [
                    Candidate(
                        node=_record_to_node(r),
                        confidence=CONF_CASEFOLD_AMBIGUOUS,
                        method="casefold_pref_ambiguous",
                    )
                    for r in casefold
                ]
                return ToolResult(
                    candidates=cands,
                    nodes=[c.node for c in cands],
                    warnings=["ambiguous"],
                    evidence=[f"esco:search:casefold_pref:{q}"],
                )

            # 4) CONTAINS on pref_label or alt_labels (case-insensitive)
            contains = self._query_match(
                session,
                labels,
                """
                MATCH (n:EscoNode)
                WHERE n.source = $source
                  AND any(l IN labels(n) WHERE l IN $labels)
                  AND (
                    toLower(n.pref_label) CONTAINS toLower($q)
                    OR any(a IN coalesce(n.alt_labels, [])
                           WHERE toLower(a) CONTAINS toLower($q))
                  )
                RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
                       n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
                       n.code AS code, n.description AS description,
                       n.alt_labels AS alt_labels, labels(n) AS labels
                ORDER BY size(n.pref_label), n.id
                LIMIT 25
                """,
                {"labels": labels, "q": q, "source": SOURCE},
            )
            if not contains:
                return ToolResult(
                    warnings=["not_found"],
                    evidence=[f"esco:search:not_found:{q}"],
                )

            cands = [
                Candidate(
                    node=_record_to_node(r),
                    confidence=CONF_CONTAINS,
                    method="contains",
                )
                for r in contains
            ]
            warnings = ["ambiguous"] if len(cands) > 1 else []
            return ToolResult(
                candidates=cands,
                nodes=[c.node for c in cands],
                warnings=warnings,
                evidence=[f"esco:search:contains:{q}"],
            )

    @staticmethod
    def _query_match(
        session: Session,
        _labels: list[str],
        cypher: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [dict(r) for r in session.run(cypher, **params)]

    def get_neighbors(
        self,
        node_id: str,
        rel_types: list[str] | None = None,
    ) -> ToolResult:
        allowed = TRAVERSABLE_RELS
        if rel_types:
            requested = {r for r in rel_types}
            bad = requested - allowed
            if bad:
                return ToolResult(warnings=[f"unknown_rel_types:{sorted(bad)}"])
            types = sorted(requested)
        else:
            types = sorted(allowed)

        with self._session() as session:
            result = session.run(
                """
                MATCH (a:EscoNode {id: $id})-[r]->(b:EscoNode)
                WHERE a.source = $source AND b.source = $source AND type(r) IN $types
                RETURN a.id AS from_id, b.id AS to_id, type(r) AS rel_type,
                       properties(r) AS rel_props,
                       b.pref_label AS pref_label, b.source AS source,
                       b.source_id AS source_id, b.uri AS uri, b.kind AS kind,
                       b.code AS code, b.description AS description,
                       b.alt_labels AS alt_labels, labels(b) AS labels
                UNION
                MATCH (b:EscoNode)-[r]->(a:EscoNode {id: $id})
                WHERE a.source = $source AND b.source = $source AND type(r) IN $types
                RETURN b.id AS from_id, a.id AS to_id, type(r) AS rel_type,
                       properties(r) AS rel_props,
                       b.pref_label AS pref_label, b.source AS source,
                       b.source_id AS source_id, b.uri AS uri, b.kind AS kind,
                       b.code AS code, b.description AS description,
                       b.alt_labels AS alt_labels, labels(b) AS labels
                """,
                id=node_id,
                types=types,
                source=SOURCE,
            )
            rows = [dict(r) for r in result]
            rows.sort(key=lambda row: (row["rel_type"], row["from_id"], row["to_id"]))
            if not rows:
                # check node exists
                exists = session.run(
                    "MATCH (n:EscoNode {id: $id}) WHERE n.source = $source RETURN n.id AS id",
                    id=node_id,
                    source=SOURCE,
                ).single()
                if not exists:
                    return ToolResult(warnings=["node_not_found"])
                return ToolResult(warnings=["no_neighbors"], nodes=[])

            nodes_map: dict[str, Node] = {}
            edges: list[Edge] = []
            # include center node
            center = _fetch_by_ids(session, [node_id]).get(node_id)
            if center:
                nodes_map[node_id] = center

            for r in rows:
                # neighbor may be from_id or to_id depending on direction
                neighbor_id = r["to_id"] if r["from_id"] == node_id else r["from_id"]
                nodes_map[neighbor_id] = _record_to_node(
                    {
                        "id": neighbor_id,
                        "pref_label": r.get("pref_label"),
                        "source": r.get("source"),
                        "source_id": r.get("source_id"),
                        "uri": r.get("uri"),
                        "kind": r.get("kind"),
                        "code": r.get("code"),
                        "description": r.get("description"),
                        "alt_labels": r.get("alt_labels"),
                        "labels": r.get("labels"),
                    }
                )
                edges.append(
                    Edge(
                        type=r["rel_type"],
                        from_id=r["from_id"],
                        to_id=r["to_id"],
                        properties=dict(r.get("rel_props") or {}),
                    )
                )

            return ToolResult(
                nodes=list(nodes_map.values()),
                edges=edges,
                evidence=[f"esco:neighbors:{node_id}"],
            )

    def enumerate_paths(
        self,
        from_id: str,
        to_id: str,
        *,
        max_depth: int = 4,
        max_paths: int = 20,
    ) -> ToolResult:
        """Return bounded, cycle-free routes with explicit pruning counts."""
        if max_depth < 1 or max_depth > MAX_PATH_DEPTH:
            return ToolResult(warnings=["invalid_max_depth"])
        if max_paths < 1 or max_paths > MAX_PATHS:
            return ToolResult(warnings=["invalid_max_paths"])

        with self._session() as session:
            ends = _fetch_by_ids(session, [from_id, to_id])
            if from_id not in ends or to_id not in ends:
                return ToolResult(warnings=["endpoint_not_found"], nodes=list(ends.values()))

            paths, pruned = self._bounded_paths(
                session,
                from_id,
                to_id,
                max_depth=max_depth,
                max_paths=max_paths,
            )

            all_ids = {from_id, to_id}
            for path in paths:
                all_ids.update(path.node_ids)
            nodes = list(_fetch_by_ids(session, list(all_ids)).values())

            warnings: list[str] = []
            if not paths:
                warnings.append("no_path")

            return ToolResult(
                nodes=nodes,
                paths=paths,
                pruning=PruningStats(
                    considered=len(paths) + pruned,
                    returned=len(paths),
                    pruned=pruned,
                ),
                meta={
                    "from_id": from_id,
                    "to_id": to_id,
                    "max_depth": max_depth,
                    "max_branching": MAX_BRANCHING,
                    "max_frontier_paths": MAX_FRONTIER_PATHS,
                },
                warnings=warnings,
                evidence=[f"esco:paths:{from_id}->{to_id}"],
            )

    @staticmethod
    def _bounded_paths(
        session: Session,
        from_id: str,
        to_id: str,
        *,
        max_depth: int,
        max_paths: int,
    ) -> tuple[list[Path], int]:
        """Breadth-first expansion with deterministic per-node and frontier caps."""
        frontier: list[Path] = [Path(node_ids=[from_id])]
        found: list[Path] = []
        pruned = 0

        for _depth in range(max_depth):
            if not frontier or len(found) >= max_paths:
                break
            frontier_ids = sorted({path.node_ids[-1] for path in frontier})
            result = session.run(
                f"""
                UNWIND $frontier_ids AS current_id
                MATCH (current:{LABEL_ESCO_NODE} {{id: current_id}})
                      -[r]-(neighbor:{LABEL_ESCO_NODE})
                WHERE current.source = $source AND neighbor.source = $source
                  AND type(r) IN $types AND neighbor.id IS NOT NULL
                RETURN current_id, neighbor.id AS neighbor_id,
                       type(r) AS rel_type, properties(r) AS rel_props,
                       startNode(r).id AS from_id, endNode(r).id AS to_id
                ORDER BY current_id,
                         CASE coalesce(r.relation_type, '')
                           WHEN 'essential' THEN 0 WHEN 'optional' THEN 1 ELSE 2
                         END,
                         type(r), neighbor.id
                """,
                frontier_ids=frontier_ids,
                source=SOURCE,
                types=sorted(TRAVERSABLE_RELS),
            )
            by_node: dict[str, list[dict[str, Any]]] = {}
            for record in result:
                row = dict(record)
                by_node.setdefault(row["current_id"], []).append(row)

            expansions: dict[str, list[dict[str, Any]]] = {}
            for node_id, rows in by_node.items():
                expansions[node_id] = rows[:MAX_BRANCHING]

            next_frontier: list[Path] = []
            for path in frontier:
                rows = by_node.get(path.node_ids[-1], [])
                pruned += max(0, len(rows) - MAX_BRANCHING)
                for row in expansions.get(path.node_ids[-1], []):
                    neighbor_id = row["neighbor_id"]
                    if neighbor_id in path.node_ids:
                        pruned += 1
                        continue
                    edge = Edge(
                        type=row["rel_type"],
                        from_id=row["from_id"],
                        to_id=row["to_id"],
                        properties=dict(row.get("rel_props") or {}),
                    )
                    candidate = Path(
                        node_ids=[*path.node_ids, neighbor_id],
                        edges=[*path.edges, edge],
                    )
                    if neighbor_id == to_id:
                        if len(found) < max_paths:
                            found.append(candidate)
                        else:
                            pruned += 1
                    else:
                        next_frontier.append(candidate)

            next_frontier.sort(key=lambda path: tuple(path.node_ids))
            if len(next_frontier) > MAX_FRONTIER_PATHS:
                pruned += len(next_frontier) - MAX_FRONTIER_PATHS
                next_frontier = next_frontier[:MAX_FRONTIER_PATHS]
            frontier = next_frontier

        # Branches still present were cut by max_depth or because max_paths was reached.
        pruned += len(frontier)
        return found, pruned

    def score_paths(self, paths: list[Path], policy: PolicyRef) -> ToolResult:
        return ToolResult(
            paths=paths,
            warnings=[
                "score_paths_not_implemented",
                "ESCO edges are binary (essential/optional); scoring is a declared "
                "policy decision, not source data. "
                f"Requested policy={policy.name!r} version={policy.version!r}.",
            ],
            meta={"policy": policy.model_dump()},
        )


# re-export rel constants for tests
__all__ = [
    "EscoSuite",
    "REL_BROADER_THAN",
    "REL_CLASSIFIED_UNDER",
    "REL_HAS_SKILL",
]
