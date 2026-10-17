#!/usr/bin/env python3
"""Run the RBG3-MOTION SPICE checks, compare them with their limits, write results.md and plots/.

Uses KiCad's bundled ngspice library (no install needed), or an `ngspice` binary on PATH.
Raw data goes to build/ (gitignored). Run: python3 sim/run.py   (from pcb/motion-board/)
"""
from __future__ import annotations

import ctypes
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
PLOTS = HERE / "plots"
KICAD_LIB = "/Applications/KiCad/KiCad.app/Contents/Frameworks/libngspice.0.dylib"

TMC_VS_OPER = 29.0      # TMC2209 VS operating max (P17 §20.1)
TMC_VS_ABS = 32.0       # absolute max (§19)
ESTOP_TRIP = 9.0        # firmware: VMOT_SENSE < 9 V -> EVT ESTOP (spec 03)
DOCKED = 20.0           # firmware: docked = DOCK_V > 20 V
ADC_FS = 2.9            # ESP32-S3 calibrated range at 12 dB (P16 Table 5-6)
VMOT_DIV = 118 / 18
DOCK_DIV = 110 / 10


# ---------------------------------------------------------------- ngspice
class Spice:
    def __init__(self):
        self.log: list[str] = []
        lib = os.environ.get("NGSPICE_LIB", KICAD_LIB)
        self.lib = None
        if Path(lib).exists():
            self.lib = ctypes.CDLL(lib)
            pr = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
            ex = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool,
                                  ctypes.c_int, ctypes.c_void_p)
            self._cbs = (pr(self._out), pr(lambda s, i, u: 0), ex(lambda *a: 0))
            self.lib.ngSpice_Init(*self._cbs, None, None, None)
        elif not shutil.which("ngspice"):
            sys.exit("ngspice not found: install KiCad, set NGSPICE_LIB, or put ngspice on PATH")

    def _out(self, s, i, u):
        self.log.append(s.decode(errors="replace"))
        return 0

    def run(self, cir: Path) -> list[str]:
        self.log = []
        if self.lib:
            self.lib.ngSpice_Command(f"source {cir}".encode())
            self.lib.ngSpice_Command(b"destroy all")
            self.lib.ngSpice_Command(b"remcirc")
        else:
            p = subprocess.run(["ngspice", "-b", str(cir)], capture_output=True, text=True)
            self.log = (p.stdout + p.stderr).splitlines()
        errs = [l for l in self.log if re.search(r"\berror\b|singular|timestep too small", l, re.I)]
        if errs:
            sys.exit(f"{cir.name}: ngspice failed:\n" + "\n".join(errs))
        return self.log


def variant(src: str, name: str, params: dict) -> Path:
    """Copy a netlist into build/ with .param overrides and OUTFILE pointing into build/."""
    text = (HERE / src).read_text()
    for k, v in params.items():
        text, n = re.subn(rf"(\.param\b[^\n]*?\b{k}=)\S+", rf"\g<1>{v}", text)
        assert n == 1, f"{src}: .param {k} not found"
    out = BUILD / name
    text = text.replace("OUTFILE", str(out))
    path = BUILD / f"{name}.cir"
    path.write_text(text)
    return path


def load(path: Path) -> dict[str, np.ndarray]:
    lines = path.read_text().splitlines()
    names = lines[0].split()
    data = np.loadtxt(lines[1:], ndmin=2)
    return {n: data[:, i] for i, n in enumerate(names)}


def crossing(t, y, level, after=0.0, falling=True):
    m = t > after
    idx = np.nonzero((y[m] < level) if falling else (y[m] > level))[0]
    return t[m][idx[0]] if len(idx) else None


# ---------------------------------------------------------------- cases
rows: list[tuple] = []  # (case, condition, result, limit, ok)


def hotplug(sp, plt):
    cases = [
        ("generic caps, 1 µH harness", dict(LH="1u", ESR470=0.15, ESR100=0.30)),
        ("generic caps, 2 µH harness", dict(LH="2u", ESR470=0.15, ESR100=0.30)),
        ("low-ESR caps, 0.3 µH harness", dict(LH="0.3u", ESR470=0.03, ESR100=0.06)),
        ("low-ESR caps, 2 µH harness", dict(LH="2u", ESR470=0.03, ESR100=0.06)),
    ]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    for i, (label, p) in enumerate(cases):
        sp.run(variant("hotplug.cir", f"hotplug-{i}", dict(RSRC=0.05, **p)))
        d = load(BUILD / f"hotplug-{i}.txt")
        t, vm, vmod, ij1, itvs = d["time"], d["v(vm)"], d["v(x1.m)"], d["i(vij1)"], d["i(vid1)"]
        vpk = max(vm.max(), vmod.max())
        ipk = ij1.max()
        dt = np.diff(t, prepend=t[0])
        i2t = float(np.sum(ij1 ** 2 * dt))
        t50 = float(np.sum(dt[ij1 > 50])) * 1e6
        rows.append(("Hot-plug", label, f"VMOT peak {vpk:.2f} V (module pins incl.)",
                     f"< {TMC_VS_OPER:.0f} V", vpk < TMC_VS_OPER))
        rows.append(("Hot-plug", label,
                     f"inrush {ipk:.0f} A peak, {t50:.0f} µs above 50 A, I²t {i2t:.2f} A²s; TVS {itvs.max()*1e3:.1f} mA",
                     "info", None))
        us = (t - 10e-6) * 1e6
        a1.plot(us, vm, label=label)
        a2.plot(us, ij1, label=label)
    a1.axhline(TMC_VS_OPER, color="r", ls="--", lw=0.8, label="TMC2209 29 V")
    a1.set_ylabel("VMOT at J1 (V)"); a1.legend(fontsize=7); a1.grid(alpha=0.3)
    a2.set_ylabel("Inrush current (A)"); a2.set_xlabel("µs after the contact closes"); a2.grid(alpha=0.3)
    a2.set_xlim(-5, 300)
    fig.suptitle("Hot-plug of a full pack (16.8 V, 50 mΩ source) onto VMOT")
    fig.tight_layout(); fig.savefig(PLOTS / "hotplug.png", dpi=110); plt.close(fig)


def estop(sp, plt):
    cases = [("drivers holding, ≈ 1 A", 16), ("≈ 0.2 A load", 84), ("drivers disabled, ≈ 20 mA", 840)]
    fig, (a0, a1, a2) = plt.subplots(3, 1, figsize=(8, 8))
    first = len(rows)
    worst = (0.0, 0.0)
    for i, (label, rl) in enumerate(cases):
        sp.run(variant("estop.cir", f"estop-{i}", dict(RLOAD=rl)))
        d = load(BUILD / f"estop-{i}.txt")
        t, vm, sense, itvs = d["time"], d["v(vm)"], d["v(sense)"], d["i(vid1)"]
        reading = sense * VMOT_DIV
        rise = vm.max() - 16.8
        trip = crossing(t, reading, ESTOP_TRIP, after=10e-6)
        worst = max(worst, (vm.max(), itvs.max()))
        trip_ms = (trip - 10e-6) * 1e3 if trip is not None else None
        rows.append(("E-stop", f"{label}: time to VMOT_SENSE < 9 V",
                     f"{trip_ms:.0f} ms" if trip_ms is not None else "> 400 ms (not reached)",
                     "info (50 ms target, backlog)", None))
        a0.plot(t * 1e3, vm, label=label)
        a1.plot(t * 1e3, vm, label=label)
        a2.plot(t * 1e3, reading, label=label)
    a1.set_ylabel("VMOT (V)"); a1.set_xlim(0, 400); a1.grid(alpha=0.3); a1.legend(fontsize=7)
    a1.set_title("first 400 ms: discharge by the remaining load", fontsize=9)
    a2.axhline(ESTOP_TRIP, color="r", ls="--", lw=0.8, label="firmware trip 9 V")
    a2.set_ylabel("Firmware VMOT reading (V)"); a2.set_xlabel("ms after the relay opens")
    a2.set_xlim(0, 400); a2.grid(alpha=0.3); a2.legend(fontsize=7)
    vpk, ipk = worst
    rows.insert(first, ("E-stop", "all coil energy into VMOT (fast decay), 16.8 V, C −20 %, any load",
                        f"VMOT rise +{vpk-16.8:.2f} V (peak {vpk:.2f} V), TVS {ipk*1e3:.2f} mA",
                        f"< {TMC_VS_OPER:.0f} V, TVS off", vpk < TMC_VS_OPER and ipk < 1e-3))
    a0.set_xlim(0, 10); a0.set_ylim(16, 17.5); a0.grid(alpha=0.3)
    a0.set_ylabel("VMOT (V)"); a0.set_title("first 10 ms: coil energy pushed into the caps", fontsize=9)
    fig.suptitle("E-stop: relay opens VMOT with the drivers carrying current")
    fig.tight_layout(); fig.savefig(PLOTS / "estop.png", dpi=110); plt.close(fig)


def backfeed(sp, plt):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    worst_dock = 0.0
    for i, (leak, imod) in enumerate([("10u", "3m"), ("1m", "10m"), ("50m", "10m")]):
        sp.run(variant("backfeed.cir", f"backfeed-{i}", dict(ILEAK=leak, IMOD=imod)))
        d = load(BUILD / f"backfeed-{i}.txt")
        vb, ib, dock = d["v-sweep"], d["ibus"], d["dock_v"]
        k = int(np.argmax(vb))
        label = f"SS54 leak {leak}A, module {imod}A"
        rows.append(("Backfeed", f"{label}, bus 16.8 V",
                     f"pack drain {ib[k]*1e3:.1f} mA ({ib[k]*16.8:.2f} W); pads {d['v(pad)'][k]:.1f} V; "
                     f"DOCK_V reads {dock[k]:.1f} V", f"DOCK_V < {DOCKED:.0f} V", dock.max() < DOCKED))
        worst_dock = max(worst_dock, dock.max())
        a1.plot(vb, ib * 1e3, label=label)
        a2.plot(vb, dock, label=label)
    a1.set_xlabel("Bus voltage (V)"); a1.set_ylabel("Current from the pack into the charger (mA)")
    a1.grid(alpha=0.3); a1.legend(fontsize=7)
    a2.axhline(DOCKED, color="r", ls="--", lw=0.8, label="'docked' threshold 20 V")
    a2.set_xlabel("Bus voltage (V)"); a2.set_ylabel("DOCK_V firmware reading (V)")
    a2.grid(alpha=0.3); a2.legend(fontsize=7)
    fig.suptitle("Charger backfeed with the dock unpowered")
    fig.tight_layout(); fig.savefig(PLOTS / "backfeed.png", dpi=110); plt.close(fig)


def signals(sp, plt):
    sp.run(variant("signals.cir", "signals", {}))
    d = load(BUILD / "signals.dc.txt")
    vin, vms, vds = d["v-sweep"], d["v(vmsense)"], d["v(docksense)"]
    at = lambda y, x: float(np.interp(x, vin, y))
    vfs = float(np.interp(ADC_FS, vms, vin))
    dfs = float(np.interp(ADC_FS, vds, vin))
    rows.append(("ADC", "VMOT_SENSE at 12.0 / 16.8 V; full scale",
                 f"{at(vms, 12):.3f} / {at(vms, 16.8):.3f} V; 2.9 V at {vfs:.1f} V",
                 "≤ 2.9 V at 16.8 V", at(vms, 16.8) <= ADC_FS))
    rows.append(("ADC", "DOCK_V at 24 V; full scale",
                 f"{at(vds, 24):.3f} V; 2.9 V at {dfs:.1f} V", "≤ 2.9 V at 24 V", at(vds, 24) <= ADC_FS))

    d = load(BUILD / "signals.tran.txt")
    t, bus = d["time"], d["v(bus)"]
    tb = 8.68e-6
    # first rising edge of the ESP frame: end of the start bit at 2 TB
    m = (t > 2 * tb) & (t < 3 * tb)
    t10 = crossing(t[m], bus[m], 0.33, falling=False)
    t90 = crossing(t[m], bus[m], 2.97, falling=False)
    rise_ns = (t90 - t10) * 1e9
    low_reply = bus[(t > 15.2 * tb) & (t < 15.8 * tb)].max()
    high_reply = bus[(t > 16.2 * tb) & (t < 16.8 * tb)].min()
    rows.append(("UART", "ESP TX through 1 k into ≈ 65 pF bus",
                 f"10–90 % rise {rise_ns:.0f} ns ({rise_ns/(tb*1e9)*100:.1f} % of a bit)", "< 5 % of a bit",
                 rise_ns < 0.05 * tb * 1e9))
    rows.append(("UART", "TMC reply against idle-high TX (100 Ω driver assumed)",
                 f"low {low_reply:.2f} V, high {high_reply:.2f} V",
                 "low < 0.83 V, high > 2.48 V (ESP32 VIL/VIH)", low_reply < 0.825 and high_reply > 2.475))

    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(t * 1e6, d["v(txp)"], lw=0.8, label="ESP TX pin")
    ax.plot(t * 1e6, bus, lw=1.2, label="UART bus / ESP RX")
    ax.axhspan(0.825, 2.475, color="0.85", label="ESP32 undefined zone")
    ax.set_xlabel("µs"); ax.set_ylabel("V"); ax.grid(alpha=0.3); ax.legend(fontsize=7, loc="lower right")
    ax.set_title("Single-wire UART: ESP sends 0x05, then a TMC2209 answers")
    fig.tight_layout(); fig.savefig(PLOTS / "uart.png", dpi=110); plt.close(fig)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    BUILD.mkdir(exist_ok=True)
    PLOTS.mkdir(exist_ok=True)
    sp = Spice()
    for case in (hotplug, estop, backfeed, signals):
        case(sp, plt)

    mark = {True: "✓ pass", False: "✗ FAIL", None: "–"}
    lines = ["# SPICE results (generated by `sim/run.py`, do not edit)", "",
             "| Case | Condition | Result | Limit | |", "|---|---|---|---|---|"]
    lines += [f"| {c} | {cond} | {res} | {lim} | {mark[ok]} |" for c, cond, res, lim, ok in rows]
    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    fails = [r for r in rows if r[4] is False]
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
