# News Tunneler — Compiled System Reference

**Designation:** ntl
**Document role:** Canonical compiled technical reference for News Tunneler (local workspace directory: `TradeForge`)
**Source:** `doc/system/`
**Build command:** `bash doc/system/BUILD.sh`
**Document version:** 1.0 (2026-09-24) — initial doc/system authored from scratch
**Protocol:** BDS Documentation Protocol v2.0

> **Generated artifact warning:** `doc/ntlSYSTEM.md` is assembled output.
> Edit the source modules under `doc/system/` and rebuild. Hand edits to
> generated artifacts are overwritten by the next build.

**Naming note:** this repo's real product identity is **News Tunneler**
(its own README, GitHub repo name, and frontend branding). The local
workspace directory name `TradeForge` is an alias only — see
`01-overview-philosophy.md`. The designation `ntl` reflects the real name.

This `doc/system/` tree is the canonical source of truth for News Tunneler.
It uses explicit **truth classes**: canonical facts define role,
architecture, and API surface; snapshot facts are dated, audit-derived
observations (test counts, current scoring weights) that must be
re-measured before reuse.

Assembly contract:

- Command: `bash doc/system/BUILD.sh`
- Validation: `bash doc/system/validate_snapshots.sh` runs during assembly
- Primary output: `doc/ntlSYSTEM.md`

| Part | File | Contents |
| --- | --- | --- |
| §1 | `01-overview-philosophy.md` | Purpose and the naming-alias disclosure |
| §2 | `02-architecture.md` | FastAPI backend + SolidJS frontend, ML/scoring pipeline |
| §3 | `03-tech-stack.md` | Stack details |
| §4 | `04-project-structure.md` | Directory layout |
| §5 | `05-config-env.md` | Required/optional environment variables |
| §6 | `06-api-contract.md` | Route groups and scoring algorithm summary |
| §7 | `07-testing.md` | Test commands |
| §8 | `90-handover.md` | Deployment notes and chapter-authoring caveats |

## Quick Assembly

```bash
bash doc/system/BUILD.sh
```
