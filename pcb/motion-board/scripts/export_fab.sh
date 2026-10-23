#!/bin/bash
# Export JLCPCB fabrication outputs to fab/: gerbers (+zip), drill, placement, BOM, schematic PDF, layout PDF, 3D renders, 3D STEP.
set -eo pipefail
cd "$(dirname "$0")/.."
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
mkdir -p fab/gerbers
$CLI pcb export gerbers -o fab/gerbers/ rbg3-motion.kicad_pcb
$CLI pcb export drill --format excellon --excellon-separate-th -o fab/gerbers/ rbg3-motion.kicad_pcb
(cd fab/gerbers && rm -f ../rbg3-motion-gerbers.zip && zip -q ../rbg3-motion-gerbers.zip ./*)
$CLI pcb export pos --format csv --units mm --side front -o fab/rbg3-motion-pos.csv rbg3-motion.kicad_pcb
$CLI sch export bom -o fab/rbg3-motion-bom.csv --fields 'Reference,Value,Footprint,${QUANTITY},${DNP}' \
  --group-by Value,Footprint rbg3-motion.kicad_sch
python3 scripts/jlc_pcba.py
$CLI sch export pdf -o fab/rbg3-motion-schematic.pdf rbg3-motion.kicad_sch
# Layout PDF for review, one page per layer with the outline: F.Cu, B.Cu, F.Fab, B.Fab, F/B silk, F/B mask.
# Scale 1.0001 instead of 1: KiCad only centres the board on the sheet when the scale is not exactly 1.
$CLI pcb export pdf --mode-multipage --include-border-title --scale 1.0001 --sketch-pads-on-fab-layers \
  --common-layers Edge.Cuts --layers F.Cu,B.Cu,F.Fab,B.Fab,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask \
  -o fab/rbg3-motion-layout.pdf rbg3-motion.kicad_pcb
for SIDE in top bottom; do
  $CLI pcb render --side $SIDE --quality high --background opaque -w 2000 -h 2000 \
    -o fab/rbg3-motion-3d-$SIDE.png rbg3-motion.kicad_pcb
done
$CLI pcb render --rotate '-45,0,45' --perspective --zoom 0.65 --quality high --background opaque -w 2400 -h 1600 \
  -o fab/rbg3-motion-3d-iso.png rbg3-motion.kicad_pcb
$CLI pcb export step --subst-models -f -o fab/rbg3-motion.step rbg3-motion.kicad_pcb
