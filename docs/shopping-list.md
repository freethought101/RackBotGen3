# Shopping list by shop (spec v0.1.17)

Ordering view of `docs/parts.csv`, grouped by shop. The orders are consolidated so most shops get several items. Prices are Tokopedia prices checked on 2026-10-10 (≈ Rp16,000 per USD). They change often, so check each one before paying. Ship to Kuta, Badung: Java sellers take ≈ 3–6 days. Links and alternatives are in `docs/sourcing-options.md`. Quantities include the listed spares.

The Tokopedia part is 22 shops (it was 33). The first 5 carry most of the order.

## Main orders (Tokopedia)

### 1. Lajarus Teknik (Cimahi): frame + Z and Y mechanics, ≈ Rp540k
- [ ] P02 2020 V-slot, 6 × 1 m (or per 10 cm cut to the CSV list), ≈ Rp302k
- [ ] P03 2040 V-slot, 420 mm (per 10 cm, Rp13k), ≈ Rp55k
- [ ] P05 T8 lead screw, **1 start, lead 2 mm**, per 10 cm: 350 mm, ≈ Rp67k
- [ ] P05 T8 anti-backlash nut, **lead 2 mm / 1 start** ×1, Rp22k
- [ ] P05 KFL08 flange bearing ×1, Rp14k
- [ ] P05 flexible coupler 5 × 8 mm ×1, Rp15k
- [ ] P06 GT2 6 mm rubber belt per metre ×1, Rp20k
- [ ] P06 idler pulley 2GT 20T **no teeth**, bore 5 mm ×1, Rp15k

### 2. Rajacell: motors + robot odds and ends, ≈ Rp940k
- [ ] P01 NEMA17 JK42HS40-1704 (1.7 A, 40 mm) ×4, Rp673k
- [ ] P16 ESP32-S3 dev board **N16R8** (or N8R2; not R8V/R16V) ×1, ≈ Rp112k
- [ ] P15 Pi camera FFC cable, **50 cm** variant ×1, Rp10k
- [ ] P08 W420 steel-ball caster ×3, Rp37k. Ask the height; it must be < 27 mm.
- [ ] P10 micro limit switch, lever, 5 A SPDT 3-pin ×15, ≈ Rp53k
- [ ] P20 4S 30 A battery protection board (BMS) ×1, Rp27k

### 3. CNC Store Bandung: power modules, E-stop, DIN parts, ≈ Rp185k
- [ ] P18 MP2482/SY8205 5 A buck (set to 5.8 V for the servos) ×1, Rp19k
- [ ] P18 XL4015 5 A CC/CV (battery charger) ×1, Rp23k
- [ ] P26 relay module 24 V, optocoupled ×1, Rp27k
- [ ] P21 robot E-stop LA38-11ZS 22 mm, self-locking ×1, Rp14k. Wire its NC contact.
- [ ] P23 active buzzer 5 V, 12 × 9.5 mm ×1, ≈ Rp5k
- [ ] P21 rocker switch 16 A, 3-pin ×1, Rp3k
- [ ] P20 pure nickel strip 0.12 × 8 mm, 10 m ×1, Rp21k
- [ ] P26 DIN rail 1 m (cut to ≈ 250 mm) ×1, Rp18k
- [ ] P26 DIN terminal block UK5N ×10, Rp25k
- [ ] *(pending decision, see "Open question")* P26 fuse terminal UK5-HESI ×1 (Rp6.5k) + 3.15 A slow-blow 5 × 20 mm fuses
- [ ] *(optional)* P09 MG90S ×3. Only if it costs ≤ Rp25k each; otherwise use shop 13.

### 4. Putra Niaga Bandung (putraniagabdg): motion board parts, ≈ Rp35k
- [ ] 0805 resistors, packs of 10: 100k, 18k, 10k, 1k, 330, 4.7k (6 packs), ≈ Rp6k
- [ ] 100 nF 0805, 10 pcs ×2, Rp5k
- [ ] Elco 100 µF 35 V **through-hole** ×5, Rp2.5k
- [ ] Elco 470 µF 35 V **through-hole** ×2, Rp3.5k
- [ ] SMBJ18A TVS ×2, Rp5k
- [ ] MMBT3904 SOT-23 ×5, Rp1.5k
- [ ] 5.08 mm 2-pin screw terminal ×2, Rp2k
- [ ] Female header 1×40 ×5, Rp10k
- [ ] Male header 1×40 ×1, Rp1k

### 5. Rajawali3D: V-wheels + pulley, ≈ Rp140k
- [ ] P04 OpenBuilds mini V-wheel with 105zz ×8, Rp101k
- [ ] P04 eccentric spacer 8 × 6 mm, 8HEX, M5 ×4, Rp27k
- [ ] P06 GT2 20T pulley, bore 5 mm, 6 mm belt ×1, Rp12k

## One- or two-item orders (Tokopedia)
These shops had no better match in the big shops above.

6. [ ] **xyz garage:** P17 MKS TMC2209 V2.0 ×5, Rp245k. UART on pin 5: JP1–JP4 are bridged on the board, nothing to solder.
7. [ ] **wirogix:** P13 IMX708 12 MP 120° camera board ×1, Rp595k. Ask about autofocus and board size.
8. [ ] **EasyWare Electro:** XY-3606 5 V / 5 A buck ×2 (P18 Pi + board, P29 router), Rp45k
9. [ ] **WKH Elektronik:** P19 2512 **R010** shunt ×2 (Rp6k) and P21 XT30 male + female pair (Rp11k)
10. [ ] **solarperfect:** P19 INA226 module ×1, Rp22k. It has the R100 shunt; swap it for the R010.
11. [ ] **teknoza:** P21 Amass XT60 pair ×1, ≈ Rp23k
12. [ ] **easy-go-512:** P21 JST-XH 230 pcs kit ×1, Rp26k. Ask whether it includes straight PCB headers.
13. [ ] **archive-oneconnection:** P09 MG90S ×3, Rp70k (unless bought at CNC Store)
14. [ ] **Putra Jaya Motor:** P38 Bosch 12 V 4-pin relay + ceramic socket ×1, Rp23k
15. [ ] **njatech:** P37 USB-A to USB-C 90° L-shape data cable ×1, Rp29k
16. [ ] **alladinshop:** P23 XT30PW-M right-angle PCB connector ×1 (Rp9k) + P21 18 AWG silicone wire, red + black 1 m each (Rp15k). Ask for 22 and 26 AWG too.
17. [ ] **i2c-parts:** P23 WS2812B 1-LED module ×2, Rp5k
18. [ ] **Elektro Bar:** P23 1N4148W SOD-123 ×5, Rp1k. Or try King Wijaya, Denpasar (local).

### Rack
19. [ ] **Mitra Otomasi:** P24 Delta DRL-24V120W1EN (Lyte II, 24 V 5 A) ×1, Rp622k. Or buy via the Delta distributor.
20. [ ] **vubil:** P31 GL.iNet GL-MT300N-V2 travel router ×1, ≈ Rp602k. A cheaper option is the TP-Link TL-WR702N, ≈ Rp355k, but it has only 1 Ethernet port and is pre-order.
21. [ ] **Akhishop:** P27 3-colour tower light 12–24 VDC ×1, Rp130k
22. [ ] **Sarana Elektric:** P28 E-stop + box + gland 22 mm ×1, Rp32k. Must have **2 NC** contacts, or add an NC contact block.

## Local shops (Bali)
- [ ] **Electronics shop** (King Wijaya Elektronik, Denpasar, also on Tokopedia):
  - P21: 7.5 A blade fuse (+ spares) + inline blade holder, SS54, and 22/26 AWG wire if alladinshop has none
  - P38: 1N4007 through-hole
  - P14: microSD 32 GB A1. Buy SanDisk Ultra or Samsung from a known shop; avoid unbranded cards.
- [ ] **Battery shop:** P20 genuine 18650 3.5 Ah ×4 (Samsung 35E or LG MJ1, ≈ Rp100–140k each; avoid the Rp45k fakes). Ask them to **spot-weld** the 4S pack with the nickel strip and BMS from shops 2 and 3. Don't solder directly to the cells.
- [ ] **Hardware store:**
  - P11 fastener kit (M5 T-nuts, screws, corner brackets, M3/M5 heat-set inserts, M3 screws + nuts)
  - P30 brass sheet 0.5 mm (dock contacts; online alternative: soember-suksess, 10 × 10 cm, Rp22k), copper sheet for the robot pads, 4-core cable ≈ 1.5 m
  - P35 steel ballast + epoxy
- [ ] **3D filament:** P32 PETG 2 kg, P33 PLA 1 kg, P34 TPU 95A 0.25 kg (also used for the drive tires)
- [ ] **Print shop:** P36 tag/label printing (matte vinyl) and a table mat of at least 1200 × 600 mm

## Open question
- **P26 3 A polyfuse:** no local through-hole polyfuse rated ≥ 30 V turned up (the 3 A ones on Tokopedia are 16 V or 24 V, too close to the 24 V rail). Recommended: a UK5-HESI DIN fuse terminal with a 3.15 A slow-blow fuse (CNC Store Bandung). It isn't resettable, so carry spare fuses. This changes the spec (02 §4), so it needs your OK.

## Overseas
- [ ] **JLCPCB:** P22 motion PCB, 5 pcs, 2 layers, 1.6 mm, from `pcb/motion-board/fab/rbg3-motion-gerbers.zip`. Ship by **DHL**.

## Only if needed (not in the budget)
- **P12 Raspberry Pi 3 Model B+** (team-owned): ≈ Rp1.06–1.19M, e.g. [tokosalim](https://www.tokopedia.com/tokosalim/raspberry-pi-3-model-b-quad-core-with-bluetooth) (250+ sold). A Rp579k listing (tronicstand) looks too cheap to trust.
- **P25 Delta DVP12SE11T PLC** (if the loan fails): ≈ Rp2.6–3.3M, e.g.:
  - [panelplcinverter](https://www.tokopedia.com/panelplcinverter/plc-delta-dvp12se11t-dvp12se-transistor-dvp) Rp2.62M
  - [plc-hmi-scada](https://www.tokopedia.com/plc-hmi-scada/dvp12se11r-dvp12se11t-delta-dvp-se-series-plc) Rp2.80M
  - [suma-automation](https://www.tokopedia.com/suma-automation/delta-dvp12se211t-dvp12se11t-plc-delta-dvp-se-series-1736495659023173308) lists it at Rp1.32M. At half the price of the others, check whether it's new, genuine and the exact SE11**T** model before buying.

  Buying the PLC would push the budget over 500 USD. The spec's fallback is the ESP32 rack controller (≈ +20 USD, 02 §4.4).

## Not to buy
- P07 bought wheels: replaced by the printed hub and tire.
- P25 PLC: loan (see above if it fails).
