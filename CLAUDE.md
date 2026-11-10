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

## Purchases (actual spend)

`docs/budget/rig-purchases.xlsx` records what was actually paid for the table rig, one row per receipt, each
checked against the receipt total. Sheets: Summary, Invoices, Items, Rig check (need vs bought), Still to buy, Notes.
- It is generated: edit the data lists in `docs/budget/build_rig_purchases.py`, then rebuild with
  `uvx --with openpyxl python docs/budget/build_rig_purchases.py docs/budget/rig-purchases.xlsx` and read the
  cross-check it prints. Don't hand-edit the xlsx.
- Receipts are in `docs/budget/invoices/` (committed at the owner's request; they show personal data and the repo
  is public), named `<date> <seller> <order no>.pdf`. The owner's working copy is `~/Downloads/Corvin invoices/`,
  with copies in its `_duplicates/` folder. New receipts arrive loose in `~/Downloads`. AirDrop resends make
  duplicate files (`marketplace N`, repeated PDFs): compare hashes, count each order once, file the original under
  that name in both places, and put it in the File column.
- Keep personal data (names, addresses, phone numbers) out of the workbook itself.
- Some entries are not plain Tokopedia receipts:
  - JLCPCB is in USD and is converted at the amount actually paid (rate cell on Invoices).
  - The FedEx import tax is in Rp.
  - "Manual" rows have no receipt.
  - Estimates go in Still to buy, not Invoices.
- This is spend tracking, separate from the planned budget in `docs/parts.csv` / Notion / `04-plan-budget-risk.md`.

## Other Notion pages
- Backlog database: `collection://44e6afc7-147e-44a9-93ea-1e0d068540f1` (live checklist; `docs/BACKLOG.md` is a snapshot).
- Email draft (PLC loan): page `3f1cbcadc6fd811eac73cf63b7e66265`.

## Hardware checks (required)

Every instruction to check, probe, solder or wire the PCB or harness comes with a marked image and numbered steps:
- Image: the owner's real photo first (`docs/images/photos/`, new ones arrive in `~/Downloads`), otherwise a 3D render, otherwise a picture of that exact part.
- Mark on the image what to touch or look at, numbered to match the steps.
- State the setup first: powered or not (USB, motor supply), what is plugged or unplugged, meter mode, parts to watch out for.
- Files: real photos go in `docs/images/photos/`, finished instruction images in `docs/images/instructions/`.
  Names are `<date>_<area>_<subject>.<ext>` in lowercase with hyphens, where area is `pcb`, `wiring` or `mechanical`
  (photos: `<date>_<part>_<view>.jpg`). The date is when it was taken or made.
- The repo is public: strip metadata from phone photos before adding them (they carry the GPS location) and crop out the room.

## Conventions
- Commit only when asked; work on branch `spec/v0.1`.
- KiCad re-saves files on open (format only); discard those unless asked.
