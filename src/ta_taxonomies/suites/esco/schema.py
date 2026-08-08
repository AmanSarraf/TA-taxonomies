"""Neo4j constraints and indexes for the ESCO suite."""

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
    f"CREATE INDEX esco_{label.lower()}_pref IF NOT EXISTS "
    f"FOR (n:{label}) ON (n.pref_label)"
    for label in (LABEL_OCCUPATION, LABEL_SKILL, LABEL_ISCO_GROUP, LABEL_SKILL_GROUP)
]


def apply_schema(driver: Driver, database: str | None = None) -> None:
    """Create constraints and indexes (idempotent)."""
    with driver.session(database=database) as session:
        for stmt in CONSTRAINTS + INDEXES:
            session.run(stmt)
