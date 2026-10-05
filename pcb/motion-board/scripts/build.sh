#!/bin/bash
# Rebuild RBG3-MOTION v1 layout: place -> bottom GND pour -> Freerouting -> import -> both pours -> DRC.
set -eo pipefail
cd "$(dirname "$0")/.."
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
JAR=${FREEROUTING_JAR:-$HOME/.kicad-mcp/freerouting.jar}
python3 scripts/fix_text.py
$PY scripts/place.py 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$PY scripts/zones.py B 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$PY scripts/route.py export 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
# Freerouting varies run to run: try a few pass limits, keep the first fully routed result.
for MP in 100 80 120 60 150; do
  java -jar "$JAR" -de build/rbg3-motion.dsn -do build/rbg3-motion.ses -mp $MP --gui.enabled=false > build/freerouting.log 2>&1
  RESULT=$(grep -E "Auto-routing stage completed" build/freerouting.log | sed 's/.*final score: //' | cut -c1-45)
  echo "freerouting -mp $MP: $RESULT"
  case "$RESULT" in *"(0 unrouted and 0 violations)"*) break ;; esac
done
$PY scripts/route.py import 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$PY scripts/stitch.py 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$PY scripts/zones.py both 2>&1 | { grep -v "wxApp\|stdpbase\|swig/python" || true; }
$CLI pcb drc --schematic-parity --severity-all -o build/drc.rpt rbg3-motion.kicad_pcb 2>&1 | grep -E "Found|violations"
