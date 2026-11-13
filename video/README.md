# Corvin films (Remotion + three.js)

Two videos for the Delta Cup 2026 presentation, both built from the real CAD (exported from `cad/src`) and
animated as pure functions of the frame, so every render is identical:

| Composition | Length | What it is | Output |
|---|---|---|---|
| `CorvinTech` | 150 s, 1080p | **Technical film for the judges**: subsystems with specs and design reasons, power tree, rack safety, full swap simulation, manufacturing. Blue look, music + SFX, no voice-over | `out/corvin-tech.mp4` |
| `RackBotPitch` | 90 s, 1080p | The earlier pitch film (orange look, synthesized music bed) | `out/rackbot-pitch.mp4` |

## Quick start

Needs Node 18+ and ffmpeg (Remotion installs its own Chrome on first render).

```bash
cd video
npm install
npm run studio          # preview and scrub in the browser, pick CorvinTech in the sidebar
npm run render:tech     # -> out/corvin-tech.mp4 (about 10 min on an M-series Mac)
npm run render          # -> out/rackbot-pitch.mp4
```

Fast checks without a full render: `node stills.mjs CorvinTech <outDir> 0.5 130 760 1420 3700` writes JPEG stills
of the given frames (30 fps, so frame = seconds × 30).

## Where to change what (`CorvinTech`, code in `src/tech/`)

| To change | Edit |
|---|---|
| Scene order and length | `TS` in `timeline.ts` (frames; keep cuts on 60-frame bars to match the 120 BPM music) |
| What the robot does (drive, lift, extractor, fingers, the swap mission) | `build()` in `timeline.ts` (keyframe engine in `src/engine.ts`) |
| Exploded view offsets, which parts glow per scene | `EXPLODE` and `FOCUS` in `timeline.ts` |
| Camera shots | `SHOT` and `keys()` in `camera.ts` (studio shots in the robot frame, floor shots in world mm) |
| On-screen text, spec rows, "why" lines, callouts | one component per scene in `scenes.tsx` |
| Power tree diagram | `diagrams.tsx` |
| Colours | `theme.ts` (poster palette) and `restyle()` in `World.tsx` (CAD colours → blue look) |
| 3D scene, lights, materials | `World.tsx` |
| Sound cues, volumes, music edit | `sfx.tsx` (`VOL`, `build()`, `MUSIC_EDIT`); `npm run cues:tech` rewrites `sfx-cues.csv` |

Every number on screen comes from the spec (`docs/spec`, v0.1.31). Cycle time and success rate are shown as
**targets**, and the mission clock as **simulated** time. Update both when the spec changes.

## Audio

- SFX: `public/sfx/sfx_XX_*.wav`, named by the ids in `PLAN-corvin-150s.md` §10. Cues are generated from the robot's
  motion and events, so retiming the robot moves its sounds too. Several files with one id (`_a`, `_b`, …) rotate as
  variations; to swap a sound, replace the file and keep its id prefix. Sources and licences (all Freesound CC0):
  `public/sfx/CREDITS.csv`.
- Music: the first file in `public/music/` ("Technology" by lNPLUSMUSIC, Pixabay licence, 120 BPM). It is
  Content ID registered: fine to play live; a YouTube upload may get a claim that the Pixabay licence clears.

## After a CAD change

Re-export the meshes (run from `cad/src`, needs `uv`):

```bash
cd cad/src
PYTHONPATH=. uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.14 python ../../video/export/export_tech_glb.py   # CorvinTech: public/models/tech/
PYTHONPATH=. uvx --no-config --managed-python --python 3.13 --from cadgen==0.7.14 python ../../video/export/export_glb.py        # RackBotPitch: public/models/
```

## `RackBotPitch` (90 s)

`src/anim.ts` (mission script), `src/camera.ts`, `src/three/World.tsx`, `src/overlays/`; scene timings in
`src/constants.ts`. Music bed: `python3 audio/make_bed.py public/audio/bed.wav`. Contact sheet: `./sheet.sh name 100 600 1400 …`.

The plan and decisions behind the technical film are in `PLAN-corvin-150s.md`.
