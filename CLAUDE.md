# TA-taxonomies

The **taxonomy layer** of Talent Angels: one suite per taxonomy (loader + graph
schema + tools) behind the shared suite contract that `TA-agents` consumes as a
versioned library.

This is a **subrepo** of the Talent Angels workspace.

## Read first

1. The workspace policy: `../CLAUDE.md`
   (or https://github.com/LFX-Talent-Angels/TA-workspace → `CLAUDE.md`).
   It is **authoritative** — git rules, DCO, secrets, agent conventions.
2. `../docs/architecture/SYSTEM.md` — cross-repo architecture + suite contract.
3. `ARCHITECTURE.md` in this repo — suite internals, ingestion pipeline,
   licensing rules. **Follow it.**
4. This file and `AGENTS.md` for code-specific rules.

## What lives here

```
src/ta_taxonomies/
├── contract/     # the typed tool surface — the ONLY thing TA-agents imports
├── suites/       # esco/ onet/ sfia/ bls/ — one owner (mentee) per suite
├── crosswalks/   # explicit cross-taxonomy links only
└── ingestion/    # shared fetch → normalize → load → validate helpers
tests/            # contract tests + load validation, run on fixtures
```

Agent/assistant code **never** lives here — that's `TA-agents`.

## Hard rules (short form — full text in ARCHITECTURE.md)

- **Pointer, not payload**: never commit licensed source text or dumps. This
  repo is Apache-2.0; the sources did not grant us redistribution rights.
  Fixtures are small, license-clean subsets.
- IDs are **suite-scoped** (`esco:…`); every node carries `source` +
  `source_id`. Codes stay strings (leading zeros!).
- Loaders are **reproducible** (`python -m ta_taxonomies.suites.<x>.load`) and
  end with validation assertions (no dangling edges, counts survive).
- `MERGE` on identity, never on bare values; attach values as properties.
- Cross-suite links live in `crosswalks/` only — explicit and cited; when no
  reliable link exists the answer is "no link", not a guess.
- Suites never import each other.

## Conventions

- **Python 3.11+.** Package is `ta_taxonomies`, src-layout (`src/`).
- Formatting/linting: **ruff**; types: **mypy** (pragmatic early on).
- Tests: **pytest**. New suite behavior ships with contract tests on fixtures.
- Configuration via env vars — see `.env.example`. **Never** commit `.env`.

## Common commands

```bash
pytest                 # contract tests on fixtures
ruff check .           # lint
ruff format .          # format
mypy src               # type-check
```

## Git

Branch + PR, **`git commit -s`** (DCO). Never push to `main`. One suite = one
owner; changes to `contract/` need mentor review (they ripple to `TA-agents`).

## AI agents

Read this file, `ARCHITECTURE.md`, and `AGENTS.md` before changing code. Review
and test agent output; you own what you submit. Record non-obvious decisions in
`TA-memory`.
