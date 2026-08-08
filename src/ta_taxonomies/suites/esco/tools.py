"""ESCO suite tools implementing the shared contract."""

from __future__ import annotations

from typing import Any

from neo4j import Driver, Session

from ta_taxonomies.contract.models import Candidate, Edge, Node, ToolResult
from ta_taxonomies.suites.esco.config import (
    CONF_CASEFOLD_UNIQUE,
    CONF_CONTAINS_OTHER,
    CONF_CONTAINS_TOP,
    CONF_EXACT_ALT,
    CONF_EXACT_PREF,
    KIND_ALIASES,
    LABEL_ISCO_GROUP,
    LABEL_OCCUPATION,
    LABEL_SKILL,
    LABEL_SKILL_GROUP,
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
        source=rec.get("source") or SOURCE,
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
        """
        MATCH (n)
        WHERE n.id IN $ids
        RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
               n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
               n.code AS code, n.description AS description,
               n.alt_labels AS alt_labels, n.skill_type AS skill_type,
               n.reuse_level AS reuse_level, n.isco_group AS isco_group,
               labels(n) AS labels
        """,
        ids=ids,
    )
    out: dict[str, Node] = {}
    for rec in result:
        node = _record_to_node(dict(rec))
        out[node.id] = node
    return out


class EscoSuite:
    """ESCO implementation of the suite contract."""

    name = SOURCE

    def __init__(self, driver: Driver, database: str | None = None) -> None:
        self._driver = driver
        self._database = database

    def _session(self) -> Session:
        return self._driver.session(database=self._database)

    def search_nodes(self, text: str, kind: str | None = None) -> ToolResult:
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
            mapped = KIND_ALIASES.get(kind.lower().replace(" ", "_"), kind)
            labels = [mapped]

        with self._session() as session:
            # 1) exact preferredLabel (case-sensitive)
            exact_pref = self._query_match(
                session,
                labels,
                """
                MATCH (n)
                WHERE any(l IN labels(n) WHERE l IN $labels)
                  AND n.pref_label = $q
                RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
                       n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
                       n.code AS code, n.description AS description,
                       n.alt_labels AS alt_labels, labels(n) AS labels
                LIMIT 25
                """,
                {"labels": labels, "q": q},
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
                MATCH (n)
                WHERE any(l IN labels(n) WHERE l IN $labels)
                  AND n.alt_labels IS NOT NULL
                  AND $q IN n.alt_labels
                RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
                       n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
                       n.code AS code, n.description AS description,
                       n.alt_labels AS alt_labels, labels(n) AS labels
                LIMIT 25
                """,
                {"labels": labels, "q": q},
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
                MATCH (n)
                WHERE any(l IN labels(n) WHERE l IN $labels)
                  AND toLower(n.pref_label) = toLower($q)
                RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
                       n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
                       n.code AS code, n.description AS description,
                       n.alt_labels AS alt_labels, labels(n) AS labels
                LIMIT 25
                """,
                {"labels": labels, "q": q},
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
                        confidence=CONF_CONTAINS_TOP if i == 0 else CONF_CONTAINS_OTHER,
                        method="casefold_pref_ambiguous",
                    )
                    for i, r in enumerate(casefold)
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
                MATCH (n)
                WHERE any(l IN labels(n) WHERE l IN $labels)
                  AND (
                    toLower(n.pref_label) CONTAINS toLower($q)
                    OR any(a IN coalesce(n.alt_labels, [])
                           WHERE toLower(a) CONTAINS toLower($q))
                  )
                RETURN n.id AS id, n.pref_label AS pref_label, n.source AS source,
                       n.source_id AS source_id, n.uri AS uri, n.kind AS kind,
                       n.code AS code, n.description AS description,
                       n.alt_labels AS alt_labels, labels(n) AS labels
                LIMIT 25
                """,
                {"labels": labels, "q": q},
            )
            if not contains:
                return ToolResult(
                    warnings=["not_found"],
                    evidence=[f"esco:search:not_found:{q}"],
                )

            cands = [
                Candidate(
                    node=_record_to_node(r),
                    confidence=CONF_CONTAINS_TOP if i == 0 else CONF_CONTAINS_OTHER,
                    method="contains",
                )
                for i, r in enumerate(contains)
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
            types = list(requested)
        else:
            types = list(allowed)

        with self._session() as session:
            result = session.run(
                """
                MATCH (a {id: $id})-[r]->(b)
                WHERE type(r) IN $types
                RETURN a.id AS from_id, b.id AS to_id, type(r) AS rel_type,
                       properties(r) AS rel_props,
                       b.pref_label AS pref_label, b.source AS source,
                       b.source_id AS source_id, b.uri AS uri, b.kind AS kind,
                       b.code AS code, b.description AS description,
                       b.alt_labels AS alt_labels, labels(b) AS labels
                UNION
                MATCH (b)-[r]->(a {id: $id})
                WHERE type(r) IN $types
                RETURN b.id AS from_id, a.id AS to_id, type(r) AS rel_type,
                       properties(r) AS rel_props,
                       b.pref_label AS pref_label, b.source AS source,
                       b.source_id AS source_id, b.uri AS uri, b.kind AS kind,
                       b.code AS code, b.description AS description,
                       b.alt_labels AS alt_labels, labels(b) AS labels
                """,
                id=node_id,
                types=types,
            )
            rows = [dict(r) for r in result]
            if not rows:
                # check node exists
                exists = session.run(
                    "MATCH (n {id: $id}) RETURN n.id AS id", id=node_id
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
        """MVP: skill-gap between occupations + depth-capped shared-skill routes."""
        if max_depth < 1:
            return ToolResult(warnings=["invalid_max_depth"])

        with self._session() as session:
            ends = _fetch_by_ids(session, [from_id, to_id])
            if from_id not in ends or to_id not in ends:
                return ToolResult(warnings=["endpoint_not_found"], nodes=list(ends.values()))

            # Skill gap for two occupations: essential skills in target not in source
            gap = session.run(
                f"""
                MATCH (a {{id: $from_id}})-[r1:{REL_HAS_SKILL}]->(s:{LABEL_SKILL})
                WHERE r1.relation_type = 'essential'
                WITH collect(DISTINCT s) AS src_skills
                MATCH (b {{id: $to_id}})-[r2:{REL_HAS_SKILL}]->(t:{LABEL_SKILL})
                WHERE r2.relation_type = 'essential' AND NOT t IN src_skills
                RETURN t.id AS id, t.pref_label AS pref_label, t.source AS source,
                       t.source_id AS source_id, t.uri AS uri, t.kind AS kind,
                       t.code AS code, t.description AS description,
                       t.alt_labels AS alt_labels, labels(t) AS labels
                LIMIT $limit
                """,
                from_id=from_id,
                to_id=to_id,
                limit=max_paths,
            )
            gap_nodes = [_record_to_node(dict(r)) for r in gap]

            # Shortest paths over traversable rels (undirected) within depth
            path_result = session.run(
                f"""
                MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
                MATCH p = (a)-[*1..{int(max_depth)}]-(b)
                WHERE all(r IN relationships(p) WHERE type(r) IN $types)
                  AND all(n IN nodes(p) WHERE n.id IS NOT NULL)
                WITH p, [n IN nodes(p) | n.id] AS ids
                RETURN ids
                LIMIT $limit
                """,
                from_id=from_id,
                to_id=to_id,
                types=list(TRAVERSABLE_RELS),
                limit=max_paths,
            )
            paths = [list(r["ids"]) for r in path_result]

            all_ids = {from_id, to_id}
            for path in paths:
                all_ids.update(path)
            all_ids.update(n.id for n in gap_nodes)
            nodes = list(_fetch_by_ids(session, list(all_ids)).values())

            warnings: list[str] = []
            if not paths and not gap_nodes:
                warnings.append("no_path")

            return ToolResult(
                nodes=nodes,
                paths=paths,
                meta={
                    "skill_gap_essential": [n.id for n in gap_nodes],
                    "skill_gap_labels": [n.label for n in gap_nodes],
                    "from_id": from_id,
                    "to_id": to_id,
                    "max_depth": max_depth,
                },
                warnings=warnings,
                evidence=[f"esco:paths:{from_id}->{to_id}"],
            )

    def score_paths(self, paths: list[list[str]], policy: str) -> ToolResult:
        return ToolResult(
            paths=paths,
            warnings=[
                "score_paths_not_implemented",
                "ESCO edges are binary (essential/optional); scoring is a declared "
                f"policy decision, not source data. Requested policy={policy!r}.",
            ],
            meta={"policy": policy},
        )


# re-export rel constants for tests
__all__ = [
    "EscoSuite",
    "REL_BROADER_THAN",
    "REL_CLASSIFIED_UNDER",
    "REL_HAS_SKILL",
]
