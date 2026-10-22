#!/bin/bash
# Rebuild RBG3-MOTION v1 layout: place -> silkscreen -> antenna keep-out -> Freerouting (GND routed as tracks, so
# no pour pocket can be cut off) -> import -> stitching vias -> both pours -> DRC.
set -eo pipefail
cd "$(dirname "$0")/.."
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
JAR=${FREEROUTING_JAR:-$HOME/.kicad-mcp/freerouting.jar}
python3 scripts/fix_text.py
$PY scripts/place.py 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
python3 scripts/silk.py
$PY scripts/zones.py none 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$PY scripts/route.py export 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
# Freerouting is deterministic for a given board (pass limits and optimiser strategies give the same result), so
# a placement change that leaves nets unrouted needs a placement fix, not a retry.
java -jar "$JAR" -de build/rbg3-motion.dsn -do build/rbg3-motion.ses -mp 100 --gui.enabled=false > build/freerouting.log 2>&1
RESULT=$(grep -E "Auto-routing stage completed" build/freerouting.log | sed 's/.*final score: //' | cut -c1-45)
echo "freerouting: $RESULT"
case "$RESULT" in
  *"(0 unrouted and 0 violations)"*) ;;
  *) grep -A2 "unrouted connection" build/freerouting.log; echo "not fully routed: adjust placement"; exit 1 ;;
esac
$PY scripts/route.py import 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$PY scripts/stitch.py 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$PY scripts/zones.py both 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$CLI pcb drc --schematic-parity --severity-all -o build/drc.rpt rbg3-motion.kicad_pcb 2>&1 | grep -E "Found|violations"
ERRORS=$(grep -c "; error" build/drc.rpt || true)
echo "DRC error-level items: $ERRORS"
[ "$ERRORS" = 0 ]
