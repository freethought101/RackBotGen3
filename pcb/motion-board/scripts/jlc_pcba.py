"""Write JLCPCB Economic PCBA files (SMD parts only) from fab/rbg3-motion-pos.csv.

Outputs fab/rbg3-motion-jlc-bom.csv and fab/rbg3-motion-jlc-cpl.csv. Through-hole parts, sockets and modules are
left out (hand-soldered). LCSC parts checked 2026-10-11: all basic, or preferred extended (no loading fee on Economic).
"""

import csv
from collections import defaultdict
from pathlib import Path

FAB = Path(__file__).resolve().parent.parent / "fab"

# (value, footprint) -> LCSC part
LCSC = {
    ("100nF", "C_0805_2012Metric"): "C49678",      # CC0805KRX7R9BB104, 50 V X7R, basic
    ("10uF", "C_0805_2012Metric"): "C15850",       # CL21A106KAYNNNE, 25 V X5R, basic (checked 2026-10-22)
    ("100k", "R_0805_2012Metric"): "C149504",      # 0805W8F1003T5E, basic
    ("18k", "R_0805_2012Metric"): "C17506",        # 0805W8F1802T5E, preferred
    ("10k", "R_0805_2012Metric"): "C17414",        # 0805W8F1002T5E, basic
    ("1k", "R_0805_2012Metric"): "C17513",         # 0805W8F1001T5E, basic
    ("330", "R_0805_2012Metric"): "C17630",        # 0805W8F3300T5E, basic
    ("4.7k", "R_0805_2012Metric"): "C17673",       # 0805W8F4701T5E, basic
    ("MMBT3904", "SOT-23"): "C20526",              # basic
    ("1N4148W", "D_SOD-123"): "C81598",            # basic
    ("SMBJ18A", "D_SMB"): "C19077573",             # preferred
}

# KiCad -> JLCPCB rotation offsets (degrees). Check every part in JLCPCB's placement preview before paying.
ROT_OFFSET = {"SOT-23": 180, "D_SMB": 180}


def main():
    with open(FAB / "rbg3-motion-pos.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r["Val"], r["Package"]) in LCSC]

    groups = defaultdict(list)
    for r in rows:
        groups[(r["Val"], r["Package"])].append(r["Ref"])
    with open(FAB / "rbg3-motion-jlc-bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (val, pkg), refs in groups.items():
            refs.sort(key=lambda s: (s[0], int(s[1:])))
            w.writerow([val, ",".join(refs), pkg, LCSC[(val, pkg)]])

    with open(FAB / "rbg3-motion-jlc-cpl.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            rot = (float(r["Rot"]) + ROT_OFFSET.get(r["Package"], 0)) % 360
            w.writerow([r["Ref"], f"{float(r['PosX']):.3f}mm", f"{float(r['PosY']):.3f}mm",
                        r["Side"].capitalize(), f"{rot:g}"])

    print(f"{len(rows)} SMD parts, {len(groups)} line items")


if __name__ == "__main__":
    main()
