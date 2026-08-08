"""Neo4j schema setup for the ESCO suite (constraints and indexes).

Use case: run once at the start of a load so ``id`` and ``uri`` are unique per
label and ``pref_label`` is indexed for search. Idempotent
(``IF NOT EXISTS``).

Why it exists: protects identity under MERGE and speeds Locate-style lookups.
Does not insert taxonomy rows — structure only, before load.py merges data.
"""

from __future__ import annotations

from neo4j import Driver

from ta_taxonomies.suites.esco.config import (
    LABEL_ISCO_GROUP,
    LABEL_OCCUPATION,
    LABEL_SKILL,
    LABEL_SKILL_GROUP,
)

# Constraints: uniqueness on suite-scoped id (and uri for provenance joins)
CONSTRAINTS: list[str] = [
    f"CREATE CONSTRAINT esco_{label.lower()}_id IF NOT EXISTS "
    f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
    for label in (LABEL_OCCUPATION, LABEL_SKILL, LABEL_ISCO_GROUP, LABEL_SKILL_GROUP)
] + [
    f"CREATE CONSTRAINT esco_{label.lower()}_uri IF NOT EXISTS "
    f"FOR (n:{label}) REQUIRE n.uri IS UNIQUE"
    for label in (LABEL_OCCUPATION, LABEL_SKILL, LABEL_ISCO_GROUP, LABEL_SKILL_GROUP)
]

INDEXES: list[str] = [
    f"CREATE INDEX esco_{label.lower()}_pref IF NOT EXISTS FOR (n:{label}) ON (n.pref_label)"
    for label in (LABEL_OCCUPATION, LABEL_SKILL, LABEL_ISCO_GROUP, LABEL_SKILL_GROUP)
]


def apply_schema(driver: Driver, database: str | None = None) -> None:
    """Create constraints and indexes (idempotent)."""
    with driver.session(database=database) as session:
        for stmt in CONSTRAINTS + INDEXES:
            session.run(stmt)
