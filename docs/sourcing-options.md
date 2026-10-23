# Sourcing options & backup cost-cutting (Indonesia)

Local sources and backup options for the parts list. Since v0.1.13 every part except the motion PCB (P22, JLCPCB) is bought locally; §3 lists the listings chosen. Shipping is to Kuta, Badung (Bali).
Prices are Tokopedia search prices checked on **2026-10-10** (≈ Rp16,000 per USD) and change often, so re-check before ordering.

## 1. Where to order

| Option | Delivery | Customs / tax | Use for |
|---|---|---|---|
| Tokopedia / Shopee (local) | Java sellers to Kuta, Bali: ~3–6 days (a Bandung seller quoted 13–16 Oct for an order on 10 Oct); Bali sellers faster | None | Everything except the PCB |
| AliExpress Choice | ~7–15 days (non-Choice 15–30+) | Parcels over USD 3: 7.5 % duty + 11 % VAT + 10 % PPh (20 % without NPWP), so ≈ +30–40 %; under USD 3: VAT only | Only parts that are much dearer locally. Group them into one order |
| JLCPCB + DHL Express | 2–3 days build + 3–5 days shipping | DHL clears customs and bills the tax | Motion PCB (P22) |
| JLCPCB Global Standard Direct | Build + ~8–15 days, sometimes ~30 | Clearance can take 5–7 working days without tracking updates | Only if time allows |

Sources: Bea Cukai [barang kiriman](https://bclampung.beacukai.go.id/artikel/hitung-pungutan-barang-kiriman/), [JLCPCB shipping](https://JLCPCB.com/help/article/65-Shipping-Info).

### Tokopedia vs AliExpress (landed = CSV estimate + ~30 %)

| Part | Tokopedia | AliExpress landed | Listing |
|---|---|---|---|
| P01 NEMA17 ×4 (JK42HS40-1704) | Rp168k each ≈ 42 USD | ≈ 47 | [rajacell](https://www.tokopedia.com/rajacell/motor-stepper-nema-17-12v-jk42hs40-1704-13a-1-7a-40mm-cnc-3d-printer-1) |
| P17 TMC2209 ×4 (MKS) | Rp49k each ≈ 12 USD | ≈ 21 | [xyzgarage](https://www.tokopedia.com/xyzgarage/makerbase-mks-tmc-2209-stepper-motor-driver-1729858504145995386) |
| P16 ESP32-S3 DevKitC-1 | Rp90–113k ≈ 6–7 USD | ≈ 13 | [Rajacell, N8R2](https://www.tokopedia.com/rajacell/esp32-s3-wifi-bluetooth-ble-5-0-esp32-s3-wifi-mesh-development-board-n8r2-n16r8-n8r2-5eec6) (Rp112.5k; N16R8 sold out 23 Oct; ships with the motors) or [sellered](https://www.tokopedia.com/sellered/esp32-s3-n8r8-n16r8-esp32-s3-devkit-type-c-esp32-s3-wroom-psram-s3-1731057903104066565). Same clone board, pinout matches the PCB; avoid the R8V/R16V variants |
| P09 MG90S ×3 | Rp23k each ≈ 4.5 USD | ≈ 10 | [archive-oneconnection](https://www.tokopedia.com/archive-oneconnectiongs/towerpro-mg90s-tower-pro-mg90s-mini-micro-servo-metal-gear) |
| P02 2020 V-slot, 6 m | ~Rp330k ≈ 21 USD | (local) | [Lajarus Teknik](https://www.tokopedia.com/lajarusteknik/aluminium-profile-2020-1-meter), also sells per 10 cm |
| P05 Tr8×2 lead screw 350 | Rp38k, screw only | ≈ 16 (set) | [IndoMakers T8-2-D8](https://www.tokopedia.com/indomakers/3d-printer-lead-screw-t8-2-d8-350mm-leadscrew-no-nut). Most "T8" listings are T8×8 (8 mm lead), so check for **lead 2**. Buy the nut, coupler and KFL08 separately |

**Batteries (P20):** Rp45k "Samsung 35E" listings are almost certainly fake (genuine cells ≈ Rp100–140k). Buy from a dedicated battery shop and don't import cells.

## 2. Camera (P13) alternatives

The chosen part is the **IMX708 120° board** ([wirogix](https://www.tokopedia.com/wirogix/imx708-12mp-high-resolution-camera-module-with-120-fov-wide-1733933892461037234), Rp595k ≈ 37 USD).
Requirements: ≥ ~65° H FOV (the approach tag is 28.6° off-axis, 01 §6.6), focus 150–700 mm, picamera2 on the Pi 3.

| Option | Price | Δ vs chosen | Trade-off |
|---|---|---|---|
| Genuine Camera Module 3 Wide, [TOKOASIA](https://www.tokopedia.com/tokoasia-id/pi-camera-module-3-120-wide-imx708-12-mp-1729941109387791340) | Rp1.218k ≈ 76 USD | +39 | Fallback if the board doesn't fit or fails |
| Genuine Camera Module 3 Wide, AliExpress | ≈ 46 USD landed | +9 | 1–2 weeks |
| IMX219 120° board, [Mikatronics](https://www.tokopedia.com/mikatronics/imx219-camera-module-for-raspberry-pi-5-8mp-120-fov) | Rp420k ≈ 26 USD | −11 | Fixed focus; `dtoverlay=imx219`; may ship with a 22-pin cable (the 15-pin P15 still fits) |
| OV5647 wide-angle, [Rajacell](https://www.tokopedia.com/rajacell/raspberry-pi-camera-5mp-ov5647-lensa-wide-angle-for-pi-3b-3b-zero-w) | Rp126k ≈ 8 USD | −29 | Confirm the FOV before buying. 130–160° fisheye lenses need OpenCV's fisheye calibration model; more distortion |

Not suitable: the standard OV5647 (54° H) and standard IMX219 v2 (62° H) are too narrow for the approach tag.

## 3. Chosen local sources (v0.1.13)

| ID | Listing(s) | ≈ Price | Notes |
|---|---|---|---|
| P04 | [mini V-wheel 105zz](https://www.tokopedia.com/search?q=OpenBuilds%20V-Wheel%20Mini%20105zz%20rajawali3d) (rajawali3d) + [mini eccentric spacers](https://www.tokopedia.com/search?q=eccentric%20spacer%20mini%208%20hex%20rajawali3d) (rajawali3d) | Rp13k × 8 + Rp7k × 4 | Mini spacer: 8 mm hex, 6 mm tall, 5 mm bore, boss for a 7.12 mm hole. The 10 mm hex / 6.35 mm spacer is for full-size wheels |
| P05 | [T8-2-D8 350](https://www.tokopedia.com/indomakers/3d-printer-lead-screw-t8-2-d8-350mm-leadscrew-no-nut) + [anti-backlash nut, lead 2](https://www.tokopedia.com/lajarusteknik/t8-nut-block-lead-screw-anti-backlash-pitch-2mm-lead-2mm-1start) + [KFL08](https://www.tokopedia.com/lajarusteknik/pillow-block-bearing-kfl08-8mm-promo) + [5×8 coupler](https://www.tokopedia.com/lajarusteknik/flexible-coupling-5-x-8mm-d20-p25-coupler-aluminium-5mm-x-8mm) | ≈ Rp89k | Lajarus Teknik also sells the 2020 extrusion |
| P06 | [GT2 6 mm belt /m](https://www.tokopedia.com/centi-store/timing-belt-gt2-6mm-untuk-3d-printer-meteran-open-loop) + [20T 5 mm pulley](https://www.tokopedia.com/rajawali3d/gt2-timing-pulley-20-teeth-bore-5mm-belt-6mm) + [toothless idler 5 mm](https://www.tokopedia.com/3dinjakarta/gearless-idler-pulley-2gt-gt2-6mm-20t-20-bore-3mm-4mm-5mm-1736902733684836117) | ≈ Rp40k | |
| P08 | [metal ball caster](https://www.tokopedia.com/bustan/universal-ball-caster-metal-free-wheel-mata-sapi-for-smart-car-arduino) × 3 | Rp15k each | Must be < 27 mm tall (ask the seller); printed spacers to 42/27 mm |
| P10 | [KW11-3Z lever](https://www.tokopedia.com/best-ay/micro-limit-switch-kw11-3z-5a-250v-3-pin-saklar-terminal-gagang-no-nc) × 15 | Rp1.4k each | |
| P11 (part: the fit-test fasteners, found 2026-10-22) | M3 heat-set insert: [PrintfyLabs brass M3](https://www.tokopedia.com/printfylabs/brass-hot-melt-heat-set-insert-nuts-knurled-m3-berbagai-ukuran-untuk-inset-baut-drat-3d-print-1731185180283995842) (M3 × 4 × 4.5 variant). M5 heat-set insert: same shop on request in chat, or [Cipta Karya 3D M2–M8](https://www.tokopedia.com/ciptakarya3d/brass-hot-melt-thread-inserts-nut-m2-m2-5-m3-m4-m5-m6-m8-double-twill-knurled-standar-internasional-gb-1pcs-1730679408596714881). M2 self-tapper: [Ada Hardware M2 × 8](https://www.tokopedia.com/adahardware/baut-pa-phillips-head-micro-screws-round-head-self-tapping-sekrup-elektronik-kayu-ujung-runcing-m2-m2-8-c9490). M3 self-tapper: [M3 tapping search](https://www.tokopedia.com/find/tapping-screw-m3) or a local hardware shop. M3 × 10: [Rajawali3D, 10 pcs](https://www.tokopedia.com/rajawali3d/baut-l-screw-socket-head-cap-m3-x-10mm-10pcs-stainless) or [3Din Jakarta](https://www.tokopedia.com/3dinjakarta/baut-m3-flat-low-profile-hitam-4-6-8-10-m3x4-m3x6-m3x8-m3x10-m3x10-66524). M5 × 10 button head: [Sepasang Baut, SS304](https://www.tokopedia.com/sepasangbaut/m5-x-10-baut-button-l-stainless-304-m5x10-1729924523835623414) or [Rajawali3D, 10 pcs](https://www.tokopedia.com/rajawali3d/baut-l-screw-socket-head-cap-m5-x-10mm-10pcs-stainless) | M3 insert ≈ Rp1.5k, M2 tapper ≈ Rp750, M3 × 10 Rp10k / 10, M5 × 10 ≈ Rp1.1k each | **Insert outer diameter must suit the pilot holes:** M3 ≈ 4.5–5.0 (pilot 4.0; an M3 × 5 × 4.2 is too loose), M5 ≈ 7 (pilot 6.4). Buy the build quantity (≈ 60 M3, ≈ 15 M5) and use a few for the hole coupon. Rajawali3D M3 × 10 showed out of stock; add the bolts to the P04 order if it's back. Prices from search snapshots, check before ordering |
| P15 | [Pi camera FFC 50 cm](https://www.tokopedia.com/rajacell/kabel-camera-ffc-cable-untuk-kamera-raspberry-pi-3b-4b-15cm-30cm-50cm-15cm) | Rp10k | Pick the 50 cm variant |
| P19 | [INA226 module](https://www.tokopedia.com/solarperfect/ina226-i2c-bi-directional-dc-current-sensor-arus) + [2512 R010 shunt](https://www.tokopedia.com/wkh-elektronik/smd-2512-alloy-resistor-r010-0-010-ohm-10mr-accuracy-1-rshunt-10milir) | Rp22k + Rp3k | Product photos show **R100**: swap the shunt (hot air or two irons) |
| P21 | [XT30/XT60](https://www.tokopedia.com/teknoza/konektor-amass-xt30-xt60-xt90-male-female-xt30-27300), [JST-XH 230 pcs](https://www.tokopedia.com/easy-go-512/isi-230pcs-kit-housing-soket-kabel-listrik-jst-xh-2-54mm-konektor-kabel-2-pin-3-pin-4-pin-5-pin-terminal-1733880946592416840), [robot E-stop 1NC twist release](https://www.tokopedia.com/rnpstore/emergency-stop-push-lock-turn-to-release-22mm-1nc-xb2-es542) | — | Fuse holder, rocker switch, SS54, silicone wire: any local electronics shop |
| P37 | [USB-A → C 90° L-shape data cable](https://www.tokopedia.com/njatech/vivan-kabel-data-gaming-90-derajat-l-style-usb-a-to-c-fast-charging-15w-3a-casan-1734418008877597777) | Rp29k | 1 m (spec 0.3 m); check the plug exits up/away from J10/J11 |
| P38 | [Bosch 12 V 4-pin relay + ceramic socket](https://www.tokopedia.com/putrajayamotor-1/relay-bosch-original-kaki-4-12v-soket-relay-keramik-kaki-4) | Rp23k | + 1N4007 |
| P18, P27, P28, P29 | see the table below | | |

P23 is itemised in §3.1. P07 (bought wheels) is replaced by printed PETG hubs + TPU tires.

### 3.1 P23 motion board components

From `pcb/motion-board/fab/rbg3-motion-bom.csv` (plus the sockets and headers the BOM leaves implicit). Order most of it
from **Putra Niaga Bandung** (putraniagabdg) to share one shipping fee. The electrolytics are **through-hole** on the board,
so don't pick the SMD "elco SMD" listings. Since v0.1.20 JLCPCB assembles the SMD parts (0805 R/C, SMBJ18A, MMBT3904,
1N4148W) on 2 boards, so those rows are optional: buy them only to build one of the 3 bare spare boards.

| BOM line | Qty (buy) | Listing | ≈ Price |
|---|---|---|---|
| 0805 resistors 100k ×2, 18k ×1, 10k ×9, 1k ×8, 330 ×3, 4.7k ×2 | packs of 10 | Putra Niaga, e.g. [10k](https://www.tokopedia.com/putraniagabdg/10pcs-resistor-smd-0805-10k-tahanan-10-000-ohm-10-k-marking-103-1729816378253083944) (same listing style for each value) | ≈ Rp1k per pack |
| 100 nF 0805 (C2, C4, C6, C8, C10–C17, C19, C21, C23) | 15 (20) | [Putra Niaga 10 pcs](https://www.tokopedia.com/putraniagabdg/10pcs-kapasitor-smd-0805-100nf-0-1uf-100n-0-1uf-104-50v-100nf-10pcs) | Rp2.4k × 2 |
| 100 µF 35 V THT (C1, C3, C5, C7; Ø8 footprint, legs bent to 3.5 mm if Ø6.3) | 4 (5) | [Putra Niaga](https://www.tokopedia.com/putraniagabdg/elco-100uf-35v-kapasitor-electrolit-polar-100-uf-35-volt-105) | Rp0.5k each |
| 470 µF 35 V THT (C9, Ø10 P5) | 1 (2) | [Tektron, Nippon Chemi-con LXZ](https://www.tokopedia.com/tektron/nippon-chemi-con-470uf-35v-lxz-series-capacitor-elko-kapasitor) | Rp1.5k each |
| 220 µF 25 V THT (C18, servo rail; Ø8 P3.5, ≤ 12 mm tall) | 1 (2) | Putra Niaga elco listings (same style as the 100 µF) | ≈ Rp0.5k each |
| 10 µF 25 V 0805 X5R (C20, C22; JLCPCB fits them, only for a bare spare) | 2 (10) | Putra Niaga 0805 capacitor listings | ≈ Rp2k per 10 |
| SMBJ18A (D1) | 1 (2) | [Putra Niaga](https://www.tokopedia.com/putraniagabdg/dioda-tvs-smbj18a-18v-600w-smb-do-214aa-supresor-diode-smbj18-marking-lt-1737854510245053736) (in stock; others are pre-order) | Rp2.4k each |
| 1N4148W SOD-123 (D2) | 1 (5) | [Elektro Bar](https://www.tokopedia.com/elektrobar/1n4148w-t4-sod-123-switching-diode-smd-sod123) | Rp0.2k each |
| MMBT3904 SOT-23 (Q1) | 1 (5) | [Putra Niaga](https://www.tokopedia.com/putraniagabdg/transistor-smd-mmbt3904-npn-sot-23-2n3904-tr-3904-sot23-marking-1am) | Rp0.3k each |
| XT30PW-M right-angle (J1) | 1 | [alladinshop](https://www.tokopedia.com/alladinshop/konektor-xt30pw-connector-xt30-male-baterai-battery-lipo-rc-tanam-pcb) or [MRI Electronics](https://www.tokopedia.com/mri-electronics/xt30pw-plug-connector-female-male-socket-1731063458330739934) | Rp9k |
| 5.08 mm 2-pin screw terminal (J2, J3) | 2 | [Putra Niaga](https://www.tokopedia.com/putraniagabdg/konektor-pcb-2p-biru-terminal-block-2pin-biru-5-08mm-2-pin-5-08) | Rp1k each |
| JST-XH board headers: 4-pin ×5, 3-pin ×7, 2-pin ×2 (+ housings, crimps) | — | P21 JST-XH 230 pcs kit (10 per size; confirm it includes the straight PCB headers), else Putra Niaga sells header + housing sets | — |
| Female header 1×40 (8 × 8-pin StepStick sockets, 2 × 22-pin DevKit sockets; a cut loses one pin) | 5 strips | [kyware](https://www.tokopedia.com/kyware/header-female-40-pin-straight-lurus-singel-row-1x40-pitch-2-54mm-warna-hitam-black) or CNC Store Bandung | Rp1.2k each |
| Male header 1×40 (servo J14, J15) | 1 | [CNC Store Bandung](https://www.tokopedia.com/cncstorebandung/pin-header-female-male-1x40-2-54mm-strip-konektor-single-row-warna-untuk-arduino-pcb-proyek-elektronika-diy-1732354605701301822) | ≈ Rp1.5k |
| WS2812B 1-LED module (on J17) | 1 (2) | [i2c-parts](https://www.tokopedia.com/i2c-parts/ws2812b-5050-rgb-led-pcb-board-1-led-module-pixel-light-5v-hitam) | Rp2.4k each |
| Active buzzer 5 V, 12 × 9.5 mm (on J19) | 1 | [CNC Store Bandung](https://www.tokopedia.com/cncstorebandung/buzzer-speaker-active-3v-5v-12x9-5mm-modul-alarm-suara-mini-for-arduino-esp32-uno-mega-nano-diy-elektronik-project-1733103146066150974) | ≈ Rp5k |

Total ≈ Rp55k (≈ 4 USD) before shipping; budgeted at 5 USD. King Wijaya Elektronik (Denpasar) also sells elcos and is
the fastest option from Bali for anything missing.

## 4. Candidates for the generic parts (first search)

| ID | Candidate | Price | Notes |
|---|---|---|---|
| P24 | [Delta DRL-24V120W1EN, Lyte II 120 W](https://www.tokopedia.com/mitra-otomasi/din-rail-power-supply-delta-drl-24v120w1en-lyte-ii-series-din-rail-120w-24v-input-1ph) | Rp622k ≈ 39 USD | DRC-24V100W1AZ (CliQ) is obsolete; its replacement is DRC-24V100W1RZ |
| P18 | [XY-3606 5 V 5 A](https://www.tokopedia.com/easyware-id/xy-3606-power-module-step-down-dc-to-dc-5a-24v-12v-to-5v-power-supply) | Rp22k | Pi + board |
| P18 | [MP2482/SY8205 5 A](https://www.tokopedia.com/cncstorebandung/dc-dc-mp2482-sy8205-5a-dc-step-down-module-7v-24v-to-5v-servo-power) | Rp19k | Servo rail. Must be adjustable to 5.8 V |
| P18 | [XL4015 5 A CC/CV](https://www.tokopedia.com/cncstorebandung/xl4015-5a-dc-dc-5v-32v-to-0-8v-30v-max-5a-step-down-cc-cv-lithium-charger-adjustable-power-supply-1731127932566144574) | Rp23k | Charger. Do the IN− to OUT− shunt check |
| P29 | [6–24 V → 5 V USB 3 A](https://www.tokopedia.com/cncstorebandung/step-down-dc-to-dc-usb-converter-6v-24v-to-5v-3a-module-usb-charger) | Rp12k | 24 V is its maximum input, so no margin. An XY-3606 + USB socket is the safer choice |
| P26 | [24 V relay module, optocoupled](https://www.tokopedia.com/cncstorebandung/module-relay-24v-high-low-trigger-with-optocoupler-1730885751716415117) | Rp27k | |
| P27 | [Hanyoung TN24-3](https://www.tokopedia.com/emelectric/hanyoung-tower-light-tn24-3-3-warna-24-vdc) / [generic 12–24 V](https://www.tokopedia.com/akhishop/tower-light-lampu-led-menara-3-warna-with-buzzer-12-24vdc-220vac-tanpa-buzzer-220vac-9905f) | Rp251k / Rp130k | Both above the 10 USD estimate; 3 panel LEDs are the −7 USD fallback |
| P28 | [E-stop + box + gland 22 mm](https://www.tokopedia.com/sarana-elektric/push-button-emergency-box-emergency-stop-set-kotak-cable-gland-22-mm-1733605650686707286) | Rp32k | Check for **2 × NC** |
| P07 | [85 mm RC wheel](https://www.tokopedia.com/rajacell/roda-robot-smart-car-85mm-blue-rc-whell-velg-ban-duri-track-off-road) + [5 mm hex hub](https://www.tokopedia.com/indo-ware/brass-hexagonal-coupling-hub-roda-ke-motor-dc-coupling-hole-2mm-3mm-4mm-5mm-6mm-7mm-8mm-shaft-haft-motor-flexible-coupling-tyre-wheel-brass-hex-coupler-5mm-f999e) | ≈ Rp37k each + hub | 85 mm instead of 80 mm, so add +2.5 mm to the caster heights; or print a hub with a TPU tire |
| P08 | [Metal ball caster](https://www.tokopedia.com/bustan/universal-ball-caster-metal-free-wheel-mata-sapi-for-smart-car-arduino) | Rp15k each | Set the height with spacers |
| P30 | [High-current pogo pins](https://www.tokopedia.com/acempoll33/2x-high-current-spring-loaded-pogo-pin-connector-1a-1-5a-2a-5a-high-power-heavy-current-battery-connector-pogopin-header-charge-1731002443373053951) | — | Brass strip from a hardware store is simpler |

## 5. Savings options (from 04 §1.5)

OV5647 wide camera instead of the IMX708 board (−29) · 3 panel LEDs instead of the tower light (−7) · team-owned filament or fasteners (−20 to −50) · drop the 3rd servo and spare switches (−5) · buy locally instead of importing (avoids ≈ 30–40 % import tax).
