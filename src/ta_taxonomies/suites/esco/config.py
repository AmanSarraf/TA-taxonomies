"""ESCO suite constants shared by the loader and tools (no I/O).

Use case: single place for Neo4j labels, relationship type names, search
``kind`` aliases, and Locate confidence scores so load.py and tools.py never
drift.

Why it exists: renaming a label or confidence policy should be one edit.
Import-only — works the same for Docker and Aura backends.
"""

from __future__ import annotations

SOURCE: str = "esco"

# Node labels stored in Neo4j
LABEL_ESCO_NODE: str = "EscoNode"
LABEL_OCCUPATION: str = "Occupation"
LABEL_SKILL: str = "Skill"
LABEL_ISCO_GROUP: str = "ISCOGroup"
LABEL_SKILL_GROUP: str = "SkillGroup"

# Relationship types (suite-canonical; map onto ARCHITECTURE vocabulary)
# HAS_SKILL carries relation_type = essential | optional
REL_HAS_SKILL: str = "HAS_SKILL"
# (narrower)-[:BROADER_THAN]->(broader)
REL_BROADER_THAN: str = "BROADER_THAN"
# (Occupation)-[:CLASSIFIED_UNDER]->(ISCOGroup)
REL_CLASSIFIED_UNDER: str = "CLASSIFIED_UNDER"
# skill ↔ skill (essential/optional in source)
REL_RELATED_TO: str = "RELATED_TO"

TRAVERSABLE_RELS: frozenset[str] = frozenset(
    {
        REL_HAS_SKILL,
        REL_BROADER_THAN,
        REL_CLASSIFIED_UNDER,
        REL_RELATED_TO,
    }
)

# kind filter values accepted by search_nodes
KIND_ALIASES: dict[str, str] = {
    "occupation": LABEL_OCCUPATION,
    "occupations": LABEL_OCCUPATION,
    "skill": LABEL_SKILL,
    "skills": LABEL_SKILL,
    "isco": LABEL_ISCO_GROUP,
    "iscogroup": LABEL_ISCO_GROUP,
    "isco_group": LABEL_ISCO_GROUP,
    "skillgroup": LABEL_SKILL_GROUP,
    "skill_group": LABEL_SKILL_GROUP,
    "skillgroups": LABEL_SKILL_GROUP,
}

# Locate confidence policy (declared; not source data)
CONF_EXACT_PREF: float = 0.95
CONF_EXACT_ALT: float = 0.90
CONF_CASEFOLD_UNIQUE: float = 0.85
CONF_CONTAINS_TOP: float = 0.70
CONF_CONTAINS_OTHER: float = 0.55
