#!/bin/bash
# Run the SPICE checks (KiCad's bundled ngspice); writes results.md and plots/. Exit 1 if any check fails.
set -eo pipefail
cd "$(dirname "$0")"
python3 run.py
