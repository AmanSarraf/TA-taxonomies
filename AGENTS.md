# AGENTS.md — TA-taxonomies

Routing for non-Claude agents (Codex, Antigravity, Cursor, Gemini, Aider, …)
working in `TA-taxonomies`, the taxonomy layer of Talent Angels.

## Read first

1. `../CLAUDE.md` — **authoritative** project policy (git, DCO,
   secrets, conventions). On GitHub: `LFX-Talent-Angels/TA-workspace`.
2. `../docs/architecture/SYSTEM.md` — cross-repo architecture + suite contract.
3. `ARCHITECTURE.md` in this repo — suite internals, ingestion pipeline,
   licensing rules. **Follow it.**
4. `CLAUDE.md` in this repo — code-specific rules.

Treat `CLAUDE.md` files as authoritative. This file only routes non-Claude
agents; keep both in sync.

## Rules (summary — see CLAUDE.md for the full text)

- Python 3.11+, src-layout package `ta_taxonomies`. Lint with ruff, test with
  pytest, type-check with mypy.
- **Pointer, not payload** — never commit licensed taxonomy text or data dumps;
  fixtures are small, license-clean subsets.
- Suite-scoped IDs; `source` + `source_id` on every node; codes stay strings.
- Reproducible loaders ending in validation assertions; MERGE on identity only.
- Cross-suite links only in `crosswalks/`, explicit and cited.
- One suite = one owner. Changes to `contract/` need mentor review.
- Branch + PR flow. Every commit DCO signed-off (`git commit -s`). Never push
  to `main`.
- Never commit `.env*` files or secrets. Use `.env.example`.
- Record non-obvious decisions/learnings in `TA-memory`.
