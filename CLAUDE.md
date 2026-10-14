# RackBotGen3 — notes for Claude

Delta Cup 2026 hot-swap robot. Spec in `docs/spec/`, CAD in `cad/` (cadgen/build123d, run with
`PYTHONPATH=src`), motion PCB in `pcb/motion-board/` (KiCad 10, rebuild with `scripts/build.sh`).

## Keep the parts list in sync (required)

The order list lives in two places that must match:
- `docs/parts.csv` (repo mirror, one row per part, stable IDs P01, P02, …)
- Notion database **Parts & Order List** — data source `collection://6f7321aa-e8e0-46b9-8ac3-b29c89561201`
  (database `17e338c2d7064c54b8c892581fef8acc`, inside the hub page `3f1cbcadc6fd8192bb31de968e109147`)

Whenever a change touches a purchased part (added, removed, quantity, spec, supplier or cost) — in the
spec, CAD (`cad/src/lib/vendor.py`, `robot_dims.py`), or the PCB BOM:
1. Update `docs/parts.csv` (keep IDs stable; new parts get the next free ID; removed parts become
   status `Not needed` instead of being deleted).
2. Update the matching Notion rows by ID (`userDefined:ID`) and set `Spec rev` to the current spec revision.
   Never overwrite `Status`, `Actual cost (USD)` or `Link` in Notion — the owner maintains those.
3. Update the budget table in `docs/spec/04-plan-budget-risk.md` §1 so the totals still match.

## Other Notion pages
- Backlog database: `collection://44e6afc7-147e-44a9-93ea-1e0d068540f1` (live checklist; `docs/BACKLOG.md` is a snapshot).
- Email draft (PLC loan): page `3f1cbcadc6fd811eac73cf63b7e66265`.

## Conventions
- Commit only when asked; work on branch `spec/v0.1`.
- KiCad re-saves files on open (format only); discard those unless asked.
