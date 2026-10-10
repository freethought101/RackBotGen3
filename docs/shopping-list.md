# Shopping list by shop (spec v0.1.14)

Ordering view of `docs/parts.csv`, grouped by shop. Prices are Tokopedia prices checked on 2026-10-10 (≈ Rp16,000 per USD). They change often, so check each one before paying. Ship to Kuta, Badung: Java sellers take ≈ 3–6 days. Links and alternatives are in `docs/sourcing-options.md`. Quantities include the listed spares.

**Before ordering:** if a shop below already has your cart open, search it for the next item too. Many of these shops (CNC Store Bandung, Rajacell, Lajarus Teknik, Putra Niaga) carry far more than listed here, and every shop you drop saves a shipping fee.

## Tokopedia

### CNC Store Bandung
- [ ] P18 MP2482/SY8205 5 A buck (set to 6 V for the servos) ×1, Rp19k
- [ ] P18 XL4015 5 A CC/CV (battery charger) ×1, Rp23k
- [ ] P26 relay module 24 V, optocoupled ×1, Rp27k
- [ ] P23 male header 1×40 ×1, ≈ Rp1.5k
- [ ] P23 active buzzer 5 V 12 × 9.5 mm ×1, ≈ Rp5k

### Putra Niaga Bandung (putraniagabdg), P23 motion board
- [ ] 0805 resistors, packs of 10: 100k, 18k, 10k, 1k, 330, 4.7k (6 packs), ≈ Rp6k
- [ ] 100 nF 0805, 10 pcs ×2, Rp5k
- [ ] Elco 100 µF 35 V **through-hole** ×5, Rp2.5k
- [ ] SMBJ18A TVS ×2, Rp5k
- [ ] MMBT3904 SOT-23 ×5, Rp1.5k
- [ ] 5.08 mm 2-pin screw terminal ×2, Rp2k

### EasyWare Electro
- [ ] XY-3606 5 V / 5 A buck ×2 (P18 Pi + board, P29 router; check that the input range reaches ≥ 30 V), Rp45k

### Lajarus Teknik (Cimahi)
- [ ] P05 T8 anti-backlash nut, **lead 2 mm / 1 start** ×1, Rp22k
- [ ] P05 KFL08 flange bearing ×1, Rp14k
- [ ] P05 flexible coupler 5 × 8 mm ×1, Rp15k
- [ ] P02 2020 V-slot 1 m ×6 (or cut to the CSV list), ≈ Rp300k; also ask about P03 2040 × 420 mm

### IndoMakers
- [ ] P05 lead screw **T8-2-D8** 350 mm (lead 2, no nut) ×1, Rp38k

### Rajawali3D
- [ ] P04 OpenBuilds mini V-wheel with 105zz ×8, Rp101k
- [ ] P06 GT2 20T pulley, 5 mm bore, 6 mm belt ×1, Rp12k

### HW Kits
- [ ] P04 eccentric spacer M5 (check it matches the mini wheel) ×4, Rp27k

### Centi Store
- [ ] P06 GT2 6 mm open belt, per metre ×1–2, Rp13k/m

### 3Din Jakarta
- [ ] P06 GT2 toothless idler, 5 mm bore, 6 mm belt ×1, Rp16k

### Rajacell
- [ ] P01 NEMA17 JK42HS40-1704 (1.7 A, 40 mm) ×4, Rp673k
- [ ] P15 Pi camera FFC cable, **50 cm** variant ×1, Rp10k

### Other robot electronics
- [ ] **xyz garage:** P17 MKS TMC2209 ×4 (+1 spare), Rp196k. Check which pin carries PDN_UART and set JP1–JP4.
- [ ] **sellered:** P16 ESP32-S3-DevKitC-1 N8R8 or N16R8 (not R8V/R16V) ×1, Rp90k
- [ ] **wirogix:** P13 IMX708 12 MP 120° camera board ×1, Rp595k. Ask about autofocus and board size.
- [ ] **archive-oneconnection:** P09 MG90S ×3, Rp70k
- [ ] **solarperfect:** P19 INA226 module ×1, Rp22k
- [ ] **WKH Elektronik:** P19 shunt 2512 **R010** 1 % ×2, Rp6k (swap it for the R100)
- [ ] **i2c-parts:** P23 WS2812B 1-LED module ×2, Rp5k
- [ ] **Tektron:** P23 470 µF 35 V Nippon Chemi-con **through-hole** ×2, Rp3k
- [ ] **Elektro Bar:** P23 1N4148W SOD-123 ×5, Rp1k
- [ ] **alladinshop** (or MRI Electronics): P23 XT30PW-M right-angle PCB connector ×1, Rp9k
- [ ] **kyware:** P23 female header 1×40 ×5, Rp6k

### Wiring and mechanical bits
- [ ] **teknoza:** P21 Amass XT30 pair ×1 and XT60 pair ×1, ≈ Rp46k
- [ ] **easy-go-512:** P21 JST-XH 2.54 230 pcs kit ×1, Rp26k. Ask whether it includes straight PCB headers.
- [ ] **rnpstore:** P21 robot E-stop 22 mm, 1 NC, twist to release ×1, Rp29k
- [ ] **Putra Jaya Motor:** P38 Bosch 12 V 4-pin relay + ceramic socket ×1, Rp23k
- [ ] **njatech:** P37 USB-A to USB-C 90° L-shape data cable ×1, Rp29k. Check the plug exits away from J10/J11.
- [ ] **best-ay:** P10 KW11-3Z lever switch ×15, Rp21k
- [ ] **bustan:** P08 metal ball caster (ask the height; must be < 27 mm) ×3, Rp44k

### Rack
- [ ] **Akhishop:** P27 3-colour tower light 12–24 VDC ×1, Rp130k
- [ ] **Sarana Elektric:** P28 E-stop + box + gland 22 mm ×1, Rp32k. Must have **2 NC** contacts, or add an NC contact block.
- [ ] **Mitra Otomasi:** P24 Delta DRL-24V120W1EN (Lyte II, 24 V 5 A) ×1, Rp622k. Or buy via the Delta distributor.

## Local shops (offline, Bali)
- [ ] **Electronics shop** (King Wijaya Elektronik, Denpasar, also on Tokopedia):
  - P21: 10 A blade fuse + holder, 10 A rocker switch, SS54, silicone wire 18/22/26 AWG
  - P38: 1N4007
  - P26: polyfuse 3 A
  - P14: microSD 32 GB A1 (SanDisk or Samsung)
- [ ] **Battery shop:** P20 genuine 18650 3.5 Ah ×4 (Samsung 35E or LG MJ1, ≈ Rp100–140k each; avoid the Rp45k fakes), 4S BMS ≥ 15 A, nickel strip
- [ ] **Hardware store:**
  - P11 fastener kit (M5 T-nuts, screws, corner brackets, M3/M5 heat-set inserts, M3 screws + nuts)
  - P26 DIN rail ≈ 250 mm and terminal blocks
  - P30 brass strip, copper sheet, 4-core cable ≈ 1.5 m
  - P35 steel ballast + epoxy
- [ ] **3D filament:** P32 PETG 2 kg, P33 PLA 1 kg, P34 TPU 95A 0.25 kg (also used for the drive tires)
- [ ] **Print shop:** P36 tag/label printing (matte vinyl) and a table mat of at least 1200 × 600 mm

## Overseas
- [ ] **JLCPCB:** P22 motion PCB, 5 pcs, 2 layers, 1.6 mm, from `pcb/motion-board/fab/rbg3-motion-gerbers.zip`. Ship by **DHL**.

## Not to buy
- P12 Raspberry Pi 3 and P31 travel router: owned.
- P25 Delta PLC: loan.
- P07 bought wheels: replaced by the printed hub and tire.
