#!/bin/bash
# Export JLCPCB fabrication outputs to fab/: gerbers (+zip), drill, placement, BOM, schematic PDF, 3D STEP.
set -eo pipefail
cd "$(dirname "$0")/.."
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
mkdir -p fab/gerbers
$CLI pcb export gerbers -o fab/gerbers/ rbg3-motion.kicad_pcb
$CLI pcb export drill --format excellon -o fab/gerbers/ rbg3-motion.kicad_pcb
(cd fab/gerbers && rm -f ../rbg3-motion-gerbers.zip && zip -q ../rbg3-motion-gerbers.zip ./*)
$CLI pcb export pos --format csv --units mm --side front -o fab/rbg3-motion-pos.csv rbg3-motion.kicad_pcb
$CLI sch export bom -o fab/rbg3-motion-bom.csv --fields 'Reference,Value,Footprint,${QUANTITY},${DNP}' \
  --group-by Value,Footprint rbg3-motion.kicad_sch
$CLI sch export pdf -o fab/rbg3-motion-schematic.pdf rbg3-motion.kicad_sch
$CLI pcb export step --subst-models -f -o fab/rbg3-motion.step rbg3-motion.kicad_pcb
