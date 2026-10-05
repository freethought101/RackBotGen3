# RackBotGen3 — Plan, Budget, Tests & Risks

Status: Draft v0.1. Today: **Mon 5 Oct 2026**. Build/test deadline **Tue 10 Nov**. Fly **Thu 12 Nov**. Final **Sat 14 Nov**.

---

## 1. Budget (USD, estimates)

Prices are typical AliExpress / local-store prices and **must be checked when ordering**. Shipping is assumed free or small (AliExpress Choice / local).

### 1.1 Robot — mechanical

| Item | Qty | USD |
|---|---|---|
| NEMA17 42×40, ≥ 0.4 N·m | 4 | 36 |
| 2020 V-slot ≈ 3.6 m + 2040 V-slot 0.45 m (robot + rack + spare station) | — | 25 |
| Mini V-wheel kits | 8 | 12 |
| Tr8×2 lead screw 400 + anti-backlash nut + coupler + KP08 | 1 | 12 |
| GT2 belt, 20T ×3, 60T ×2, idler | set | 15 |
| 8 mm shaft + KFL08 ×4 | set | 10 |
| Wheels 80 mm, 8 mm bore | 2 | 10 |
| Casters | 2 | 5 |
| MG90S servo | 3 | 8 |
| Lever microswitches KW11-3Z | 12 | 6 |
| Fastener kit (M5 T-nuts/screws, corner brackets, M3 + heat-set inserts) | — | 20 |
| **Subtotal** | | **159** |

### 1.2 Robot — electronics

| Item | Qty | USD |
|---|---|---|
| Raspberry Pi 3B/3B+ | 1 | 0 (team-owned) |
| Raspberry Pi Camera Module 3 **Wide** | 1 | 35 |
| microSD 32 GB A1 | 1 | 8 |
| CSI flex cable 500 mm | 1 | 3 |
| ESP32-S3-DevKitC-1 | 1 | 10 |
| TMC2209 StepStick | 4 | 16 |
| Buck 5 V/5 A + buck 6 V/3 A + CC/CV charger module | 3 | 12 |
| INA226 module | 1 | 4 |
| 18650 3.5 Ah × 4 + 4S BMS + holder/nickel strip | set | 30 |
| XT60/XT30, fuse holder, rocker switch, robot E-stop, silicone wire, JST-XH kit | set | 25 |
| Motion PCB, JLCPCB 5 pcs + shipping | 1 | 25 |
| Passives, headers, StepStick sockets, TVS, caps, WS2812, buzzer | set | 12 |
| **Subtotal** | | **180** |

### 1.3 Rack & spare station — electrical

| Item | Qty | USD |
|---|---|---|
| **Delta 24 V DIN-rail PSU, 75–100 W** | 1 | 35 |
| DIN rail, terminal blocks, 24 V relay module, polyfuse | set | 10 |
| 24 V mini tower light R/Y/G | 1 | 10 |
| Rack E-stop (2 NC contacts) | 1 | 8 |
| 24 → 5 V USB buck (router) | 1 | 3 |
| Dock contacts (pogo/brass), copper sheet, spare-station cable | set | 8 |
| Travel router | 1 | 0 (borrow/owned; ≈ 25 if bought) |
| **Delta DVP-12SE11T PLC** | 1 | **not in budget, loan/sponsor** (≈ 150–250) |
| **Subtotal** | | **74** |

### 1.4 Printing & demo materials

| Item | USD |
|---|---|
| PETG 2 kg | 36 |
| PLA 1 kg | 15 |
| TPU 95A 0.25 kg | 8 |
| Steel ballast + epoxy (dummy drives) | 8 |
| Tag/label printing, table mat | 10 |
| **Subtotal** | **77** |

### 1.5 Total

| | USD |
|---|---|
| Robot mechanical | 159 |
| Robot electronics | 180 |
| Rack electrical | 74 |
| Printing & demo | 77 |
| **Total** | **≈ 490** (of 500) |

The margin is thin. **Savings options** (use them if prices come in higher, or a router must be bought):
TPU-printed wheels instead of bought (−10) · wide-angle OV5647 camera instead of Module 3 Wide (−20, more distortion) ·
3 panel LEDs instead of the tower light (−7) · team-owned filament or fasteners (−20 to −50) · drop the 3rd servo and spare switches (−5).
**PLC**: request a loan from Delta Thailand this week. If none, use the ESP32 fallback rack controller (≈ +20 USD, see 02 §4.4).

## 2. Schedule

```mermaid
gantt
  dateFormat  YYYY-MM-DD
  axisFormat  %d %b
  title RackBotGen3 — 5 Oct to 12 Nov 2026

  section Spec & sourcing
  Spec review and freeze            :a1, 2026-10-05, 3d
  Ask Delta for PLC loan            :milestone, 2026-10-06, 0d
  Order all parts (deadline)        :milestone, 2026-10-08, 0d
  Parts in transit                  :a2, 2026-10-08, 12d

  section Mechanical (CAD to print)
  CAD caddy, dummy, shelf           :m1, 2026-10-07, 3d
  Print and fit-test caddy/shelf    :m2, after m1, 3d
  CAD rack + spare station          :m3, 2026-10-08, 4d
  CAD robot (base, Z, Y, tray)      :m4, 2026-10-08, 7d
  Print rack + robot parts          :m5, 2026-10-12, 8d
  Build rack + spare station        :m6, 2026-10-16, 4d
  Build robot base + drive          :m7, 2026-10-19, 4d
  Build Z lift + Y extractor + tray :m8, 2026-10-21, 5d

  section Electrical
  KiCad motion board                :e1, 2026-10-07, 6d
  PCB order (deadline 14 Oct)       :milestone, 2026-10-13, 0d
  PCB fab and shipping              :e2, 2026-10-13, 10d
  Breadboard bench rig (modules)    :e3, 2026-10-16, 5d
  Assemble + test PCB               :e4, 2026-10-23, 3d
  Rack wiring + PLC program         :e5, 2026-10-19, 6d

  section Software
  Pi app in sim mode + dashboard    :s1, 2026-10-08, 12d
  Motion firmware                   :s2, 2026-10-12, 11d
  Vision: calibration + docking     :s3, 2026-10-22, 7d

  section Integration & test
  Integration, first full swap      :i1, 2026-10-27, 6d
  First full swap                   :milestone, 2026-11-01, 0d
  Feature freeze                    :milestone, 2026-11-02, 0d
  50-cycle reliability + fixes      :i2, 2026-11-03, 5d
  Demo video (backup, required)     :i3, 2026-11-06, 3d
  Pitch deck + rehearsal            :i4, 2026-11-03, 7d
  Pack test + weigh bags            :i5, 2026-11-09, 2d
  Fly to Thailand                   :milestone, 2026-11-12, 0d
```

Key rule: **order everything by 8 Oct**. Buy motors, extrusion and fasteners locally if AliExpress delivery is quoted at more than 10 days.
Until parts arrive, software runs in sim mode and mechanical fit is tested with printed parts only.

## 3. Test protocol & acceptance criteria

| ID | Test | Pass criterion | When |
|---|---|---|---|
| T1 | Caddy fit in bay shelf and tray | Slides in/out by hand with ≤ 5 N, no binding, 10/10 | W1–W2 |
| T2 | Dummy drive mass | 600 ± 30 g, lid secure after a 1 m drop onto foam | W2 |
| T3 | Z homing and holding | Repeatability ±0.1 mm (20×). 2 kg payload, unpowered, no creep in 10 min | W3 |
| T4 | Y pull/push on bench | 20/20 pulls and pushes from a fixed bay, finger engages every time | W3 |
| T5 | Drive accuracy | 500 mm straight: error < 10 mm. 180° turn: error < 3° (10×) | W3 |
| T6 | Docking | Start 700 mm away, ±50 mm lateral, ±10° heading → 20/20 docks, X repeatability ±2 mm | W4 |
| T7 | Bay fine-alignment | Residual Z error ≤ 1 mm after correction (20×) | W4 |
| T8 | Vision performance | ≥ 8 fps at 640×480 on the Pi 3 while the dashboard streams | W3–W4 |
| T9 | PLC / rack | All I/O match the map. Watchdog trips in 2 ± 0.5 s. Dock power only with dock + E-stop OK | W3–W4 |
| T10 | E-stop | Robot motion stops < 0.2 s. Mission recovers via re-home + resume | W4 |
| T11 | **Full swap** | Cycle ≤ 3 min. **≥ 48/50 cycles** without manual intervention | W5 |
| T12 | Battery & charging | 1 h continuous cycling, cells ≥ 3.5 V. Charging confirmed on dock (I < 0) | W5 |
| T13 | Dashboard | All views live on a laptop + phone. Fault injection → auto job → bay OK | W4–W5 |
| T14 | **Pack test** | Every bag ≤ 7 kg incl. personal items. Reassembly ≤ 20 min + calibration ≤ 10 min from a written checklist | W5 |

Log every swap (timestamp, result, cycle time, Wh) in SQLite. The data goes into the pitch (reliability and energy charts).

## 4. Risk register

| # | Risk | L | I | Mitigation / fallback |
|---|---|---|---|---|
| R1 | Parts arrive late | H | H | Order by 8 Oct, local suppliers for motors/extrusion, 1 spare of each cheap part |
| R2 | PCB late or faulty | M | M | Perfboard build of the same schematic and pinout. Breadboard bench rig from W2 |
| R3 | No PLC available | M | M | ESP32 rack controller with the identical Modbus map (02 §4.4). Delta PSU stays as the Delta part |
| R4 | Docking unreliable | M | H | Mechanical funnel does the fine work. Slow final approach. Automatic retries. Tune in W4 |
| R5 | Caddy binds in bay or tray | M | H | Lead-ins, fit test in W1–W2 before printing everything, sand or PTFE tape, adjust `Z_*_OFFSET` |
| R6 | Pi 3 vision too slow | L | M | ROI crop, decimate, lower approach speed. Fallback: a Pi 4 borrowed or bought |
| R7 | Battery issue at the airport | L | H | 50 Wh labeled, datasheet printed, in cabin. **Fallback: tethered power** from the rack PSU (2 m lead into the charger input, ≈ 25 W) |
| R8 | Transport damage | M | H | Padded packing, spare printed parts (fingers, nose, shelf), spare servos/switches, STL files on a laptop |
| R9 | Integration overrun | H | H | Sim-first software. Feature freeze 2 Nov. **Single-slot fallback** (two trips, same hardware) |
| R10 | Scope creep | M | M | One owner per subsystem. Stretch goals (MQTT, auto-charge tuning, HMI) only after T11 passes |

## 5. Airline & travel checklist

- [ ] **Battery**: 4S1P 18650 = 50.4 Wh (< 100 Wh, no airline approval needed). **Carry-on only**, Wh written on the pack, XT60 capped, in a LiPo bag. Printed cell datasheet and Wh calculation.
- [ ] No spare loose cells. If spares are needed, buy in Thailand or bring at most 2, each in a separate case.
- [ ] Check each member's airline: 7 kg and 56 × 36 × 23 cm (AirAsia-type limits are the strictest).
- [ ] Tools: no knives, cutters or scissors. Screwdrivers and wrenches over ~7 cm are banned on some airlines. Bring short hex keys and bits only, or buy a cheap screwdriver set in Thailand.
- [ ] No butane soldering iron. Leave the soldering iron at home or put it in checked baggage.
- [ ] One-page device description ("educational robot prototype for Delta Cup 2026, no hazardous materials") + Delta invitation letter for security and customs.
- [ ] Thailand mains 220 V / 50 Hz, sockets A/B/C/O. The Delta PSU is universal input. Bring 2 plug adapters and a power strip.
- [ ] Wi-Fi router SSID and IPs unchanged. Dashboard tested offline (no internet needed).
- [ ] Laptop with: STL files, firmware build, Pi SD card image backup, ISPSoft project, demo video (backup), pitch deck.
- [ ] National flag (required by the guidebook) + university flag.
- [ ] Reassembly and calibration checklist printed.
