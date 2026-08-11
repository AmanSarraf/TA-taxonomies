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

| Rel | Meaning |
| --- | --- |
| `HAS_SKILL` | Occupation → Skill; property `relation_type` = `essential` \| `optional` |
| `BROADER_THAN` | narrower → broader (ISCO / skill hierarchy) |
| `CLASSIFIED_UNDER` | Occupation → ISCOGroup |

## Tools

`EscoSuite` implements the contract: `search_nodes`, `get_neighbors`,
`enumerate_paths`, `score_paths` (not implemented — ESCO has no native weights).
