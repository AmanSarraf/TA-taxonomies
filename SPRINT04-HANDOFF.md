# Sprint 4 MVP — session handoff (ESCO / TA-taxonomies)

**Last updated:** 2026-08-08  
**For:** New Grok (or other agent) sessions started with cwd = `TA-taxonomies`  
**Owner context:** AmanSarraf · LFX Talent Angels

---

## How to use this file

In a new session, say only:

```text
Read SPRINT04-HANDOFF.md and continue from "Next actions".
```

Or:

```text
@SPRINT04-HANDOFF.md Continue Sprint 4 ESCO MVP from the next actions.
```

---

## Goal (Sprint 4)

Ship a **headless MVP** that:

1. Loads **ESCO** into Neo4j (local Docker by default).
2. Exposes suite tools, then Locate → Connect → Pathfind **skills** under one main assistant (`TA-agents` later).
3. Instruments **token/compute cost** (JSONL + scale-up estimates).
4. Explores efficiency (caching, tool-only vs NL, provider-agnostic LLM).

**Not in scope for this workstream:** `TA-app` UI, `TA-site` landing page, multi-taxonomy, VC/Learning Tokens issuance, always-on 3 peer subagents.

---

## Locked decisions

| Topic | Decision |
| --- | --- |
| Taxonomy | **ESCO only** |
| Graph host | **Local Docker Compose (Neo4j 5)** default; Aura optional via `NEO4J_URI` |
| L / C / P | **Capabilities**; default **skill + tools** under one main assistant; subagent only if isolation is measured later |
| MVP packaging | Skills only for L/C/P — no always-on subagents |
| Suite tools | Shared contract: `search_nodes`, `get_neighbors`, `enumerate_paths` (specialize per leaf; not identical free-for-all toolbelts) |
| Build order | KG + tools in **TA-taxonomies** first → then **TA-agents** (Locate + cost = Gate A) |
| LLM | Provider-agnostic (`LLM_PROVIDER` / env); stub `none` for offline |
| Observability | JSONL run log required; LangSmith/Langfuse optional |

---

## Data location (already on disk)

```text
data/esco/                          # gitignored via /data/
├── README.md
├── ESCO-KNOWLEDGE-GRAPH-20260808.zip
└── raw/
    ├── DATABASE/                   # 19 ESCO English *.xlsx
    ├── neo4j_importer_model_2026-08-03 (4).json
    └── data-importer-2026-08-03.zip
```

**Absolute path:**

`/Users/amansarraf/Developer/github.com/AmanSarraf/TA-workspace/TA-taxonomies/data/esco/`

Core files for MVP load (after completeness check):

- `occupations_en.xlsx`
- `skills_en.xlsx`
- `ISCOGroups_en.xlsx`
- `skillGroups_en.xlsx`
- `occupationSkillRelations_en.xlsx`
- `broaderRelationsOccPillar_en.xlsx`
- `broaderRelationsSkillPillar_en.xlsx`
- (optional later: `skillSkillRelations_en.xlsx`, green/digital collections, …)

**Rules:** do not commit full dumps; pointer-not-payload; ESCO CC BY 4.0 attribution when publishing.

---

## Full plan document

Detailed research + phased plan (Rev 4):

```text
/Users/amansarraf/Developer/github.com/AmanSarraf/TA-workspace/TA-lab/mentees/AmanSarraf/sprint-04/scratch/MVP-RESEARCH-AND-PLAN.md
```

Also useful:

| Doc | Path |
| --- | --- |
| Use cases / why MVP measures cost | `TA-lab/mentees/AmanSarraf/sprint-04/scratch/USE-CASES-INTEGRATION.md` |
| ESCO KG notes (PDF) | `TA-lab/mentees/AmanSarraf/sprint-04/scratch/info_KG_ESCO.pdf` |
| Alejandro Sprint 1 ESCO | `TA-lab/mentees/alejandrokantun81/sprint-01_alexkantun/` (NOTES.md, sample cypher) |
| System architecture | `TA-workspace/docs/architecture/SYSTEM.md` |
| ADR-0003 (skills, not peer agents) | `TA-workspace/docs/decisions/0003-agent-plus-skills-architecture.md` |
| Sprint 2 architecture (PR #12) | branch `mentee/AmanSarraf/sprint-02` → `mentees/AmanSarraf/sprint-02/ARCHITECTURE.md` |

---

## Repo map

| Step | Repo | Work |
| --- | --- | --- |
| 0–2 | **TA-taxonomies** (you are here) | Docker Neo4j, ESCO suite, fixture, loader, contract tools |
| 3–4 | **TA-agents** | Locate/Connect/Pathfind skills, FastAPI `/v1`, cost log, bench |
| — | TA-app / TA-site | Skip |

---

## Next actions (do in order)

### Done this session (2026-08-08)

1. **Completeness analysis** → `data/esco/COMPLETENESS.md` (gitignored under `/data/`)
2. **Step 0** → `docker-compose.yml` (Neo4j 5), `.env.example` defaults, container `ta-neo4j` healthy
3. **Step 1** → ESCO suite: `schema.py`, `load.py`, `tools.py`, ICT fixture, `python -m ta_taxonomies.suites.esco.load --mode fixture`
4. **Step 2a** → `search_nodes` + contract tests (`tests/suites/esco/`) — green with Neo4j

### 5. Optional polish in TA-taxonomies *(if needed before agents)*

- `get_neighbors` / `enumerate_paths` deeper tests (stubs exist)
- Full load smoke: `pip install openpyxl` + `--mode full` (slow; gitignored data)
- Branch + PR: `mentee/AmanSarraf/sprint-04-esco-suite` with DCO

### 6. Later (new session in **TA-agents**)

Locate skill + FastAPI `/v1` + JSONL cost + golden set → Connect → Pathfind.

---

## Explicit non-goals (do not drift)

- Scaffolding a frontend in TA-app  
- Full multi-suite fan-out  
- Three always-on subagents with identical toolbelts  
- Committing ESCO xlsx dumps  
- Blocking on Aura or LangSmith  

---

## Git

- Branch pattern e.g. `mentee/AmanSarraf/sprint-04-esco-suite`  
- `git commit -s` (DCO)  
- Never push `main`  
- Never commit `.env` or `data/` dumps  

---

## One-line status

**ESCO fixture loads into local Neo4j; `search_nodes` contract tests green. Next: optional full-load smoke / PR this repo, then Gate A in TA-agents (Locate + cost).**
