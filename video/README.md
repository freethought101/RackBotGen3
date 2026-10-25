# RackBot Gen3 — pitch film (90 s)

The motion-design pitch video for the Delta Cup 2026 presentation. The robot, rack and spare station are the
real CAD (exported from `cad/src`), animated through the spec's swap workflow (`docs/spec/00-overview.md` §6),
with the extractor rules from `03-software.md` §5.1 (only the working finger is engaged during a Y stroke).

| Step | Command (from `video/`) |
|---|---|
| Re-export the CAD meshes after a CAD change | `PYTHONPATH=../cad/src uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.14 python export/export_glb.py` |
| Regenerate the music bed | `python3 audio/make_bed.py public/audio/bed.wav` |
| Preview / scrub | `npm run studio` |
| Render | `npm run render` → `out/rackbot-pitch.mp4` |
| Contact sheet of frames | `./sheet.sh name 100 600 1400 …` |

Structure: `src/anim.ts` (mission script: robot pose, Z/Y/fingers, caddy hand-offs, PLC events),
`src/camera.ts` (camera path), `src/three/World.tsx` (3D scene), `src/overlays/` (typography, HUD, callouts).
Scene timings are in `src/constants.ts` (cuts fall on 120 BPM bar lines).

Every number on screen comes from the spec. Cycle time and success rate are shown as **targets**, and the
mission clock is labelled as simulated time.
