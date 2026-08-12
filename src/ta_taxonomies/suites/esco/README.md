# ESCO suite

European Skills, Competences, Qualifications and Occupations taxonomy.

## Source & license

- **Source:** ESCO (European Commission)
- **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Attribution:** When publishing derived public materials, credit ESCO / European Commission.

This suite follows the repo **pointer-not-payload** rule: full dumps are never
committed. Local files live under `data/esco/` (gitignored). Tests use the small
committed fixture under `fixtures/`.

## Load

```bash
# Local Neo4j (default)
docker compose up -d
cp .env.example .env   # NEO4J_PASSWORD=taxonomies-dev

# Fixture (CI / contract tests)
python -m ta_taxonomies.suites.esco.load --mode fixture

# Full English DATABASE xlsx (local only)
export ESCO_DATA_DIR=data/esco/raw/DATABASE
python -m ta_taxonomies.suites.esco.load --mode full
```

## Graph model (MVP)

| Label | Identity |
| --- | --- |
| `Occupation` | `id` = `esco:occupation:…`, `uri`, `source`, `source_id` |
| `Skill` | `id` = `esco:skill:…` |
| `ISCOGroup` | `id` = `esco:isco:<code>` (code from URI, string) |
| `SkillGroup` | `id` = `esco:…` |

All ESCO nodes also carry the internal `EscoNode` label. Its unique `id`
constraint gives mixed-kind lookups an indexed anchor without treating shared
canonical labels such as `Occupation` or `Skill` as ESCO-only.

| Rel | Meaning |
| --- | --- |
| `HAS_SKILL` | Occupation → Skill; property `relation_type` = `essential` \| `optional` |
| `BROADER_THAN` | narrower → broader (ISCO / skill hierarchy) |
| `CLASSIFIED_UNDER` | Occupation → ISCOGroup |

## Tools

`EscoSuite` implements the contract: `search_nodes`, `get_neighbors`,
`enumerate_paths`, `score_paths` (not implemented — ESCO has no native weights).

Search returns exact/alias/case-insensitive/substring matches in that order.
Every result group has deterministic ordering and one confidence per match
method; an unknown `kind` is reported instead of being used as a graph label.

Path enumeration is cycle-free and deliberately bounded for ESCO's high-degree
skill hubs: depth at most 6, at most 25 expansions per node, a 500-path frontier,
and at most 100 returned paths. Essential edges are considered before optional
edges; ties use relationship type and node ID. `ToolResult.pruning` reports how
many branches were cut. These priorities are Talent Angels traversal policy,
not weights published by ESCO.
