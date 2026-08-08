"""ESCO suite configuration: traversable relationships and kinds."""

from __future__ import annotations

SOURCE = "esco"

# Node labels stored in Neo4j
LABEL_OCCUPATION = "Occupation"
LABEL_SKILL = "Skill"
LABEL_ISCO_GROUP = "ISCOGroup"
LABEL_SKILL_GROUP = "SkillGroup"

# Relationship types (suite-canonical; map onto ARCHITECTURE vocabulary)
# HAS_SKILL carries relation_type = essential | optional
REL_HAS_SKILL = "HAS_SKILL"
# (narrower)-[:BROADER_THAN]->(broader)
REL_BROADER_THAN = "BROADER_THAN"
# (Occupation)-[:CLASSIFIED_UNDER]->(ISCOGroup)
REL_CLASSIFIED_UNDER = "CLASSIFIED_UNDER"

TRAVERSABLE_RELS: frozenset[str] = frozenset(
    {
        REL_HAS_SKILL,
        REL_BROADER_THAN,
        REL_CLASSIFIED_UNDER,
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
CONF_EXACT_PREF = 0.95
CONF_EXACT_ALT = 0.90
CONF_CASEFOLD_UNIQUE = 0.85
CONF_CONTAINS_TOP = 0.70
CONF_CONTAINS_OTHER = 0.55
