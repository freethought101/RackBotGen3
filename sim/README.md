# Corvin swap simulator (final-round demo)

Interactive browser simulation of the hot-swap robot for the judges: 3D view built from the real CAD meshes,
the IIoT dashboard (03-software §7) and the robot's own camera view with AprilTag detections.
It runs fully in the browser, offline, with no Python or server.

| Step | Command (from `sim/`) |
|---|---|
| Install | `npm install` |
| Develop | `npm run dev` → http://localhost:5173 |
| Headless check (mission invariants, ~5 s) | `npm run check` |
| Stage build | `npm run build` → **`dist/index.html`**, one ≈ 10 MB file that opens by double-click, offline |

The meshes come from `video/public/models/*.glb` (re-export them after a CAD change, see `video/README.md`).

## What is simulated, and from where

- **Mission**: `src/core/mission.ts` is a port of `rackbot/rackbot/mission.py`: job preconditions, the seven
  states, pull/push with the one-working-finger rule, goto (undock, turn, tag approach, funnel DOCK), tag-lost
  back-off (3 retries) → `FAULT`, operator resume.
- **Approach controller**: `approach_step()` from `rackbot/vision.py` (03 §6.2), fed by a pinhole model of the
  IMX708 (102° HFOV, 640×480): a tag counts as seen only when it is in frame, facing the camera and ≥ 8 px.
  TURN has the sim's 3° overshoot, so the controller has real work to do.
- **Speeds and geometry**: `src/core/spec.ts` (`config.yaml`, `cad/src/lib/dims.py`, `video/src/constants.ts`).
- **PLC**: the 03 §4 ladder and register map (D0–D3, M0–M2, lamps, dock-power interlock).
- **Health / energy**: ports of `health.py` (WARN at 10, FAILED at 50 reallocated sectors over 10 s) and the
  02 §1 power numbers (50.4 Wh pack, idle ≈ 4 W, moving 12–20 W, 1.5 A dock charger).
- **Not real**: the data hall is a scaled concept (4 racks, one robot), RAID rebuild is time-lapsed to 60 s,
  and the "technician restock" is a 30 s timer. All times are simulated time.

Simulated cycle: ≈ 82 s per swap in the arena (700 mm), ≈ 108 s in the hall (spec target ≤ 3 min).

## Demo script (about 4 minutes)

1. **Data hall, 4×.** Click any drive (in the Drives card or on the caddy in 3D). SMART goes WARN → FAILED, RAID
   degrades and the job queues by itself. Switch to **Follow robot**: pick the spare, drive the aisle, tag
   approach (watch d / x / θ / ψ in the camera view), funnel dock, caddy-ID check, extract, insert, return the failed drive to RMA, charge.
   The stepper keeps the cycle-time breakdown.
2. **E-STOP** (or the space bar) during a Y stroke: everything freezes and the lamp goes red. Release → **Resume**.
3. **Block camera** during an approach: tag lost → stop, back off 100 mm, retry ×3 → `FAULT(E_TAG_LOST)`.
   Unblock → **Resume**.
4. **Random failures** at 16×: jobs queue, wait for the restock, and the KPIs fill in (cycle, fault → new drive,
   Wh per swap, degraded time).
5. **Competition arena**: the same code on exactly the table we brought.
