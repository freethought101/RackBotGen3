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
| P16 ESP32-S3 DevKitC-1 | Rp90–110k ≈ 6–7 USD | ≈ 13 | [sellered](https://www.tokopedia.com/sellered/esp32-s3-n8r8-n16r8-esp32-s3-devkit-type-c-esp32-s3-wroom-psram-s3-1731057903104066565) (avoid the R8V/R16V variants) |
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
| P04 | [mini V-wheel 105zz](https://www.tokopedia.com/search?q=OpenBuilds%20V-Wheel%20Mini%20105zz%20rajawali3d) (rajawali3d) + [M5 eccentric spacers](https://www.tokopedia.com/hwkits/openbuilds-spacer-eccentric-10hex-m5-for-v-wheel) | Rp13k × 8 + Rp7k × 4 | Check that the spacer fits the mini wheel bore |
| P05 | [T8-2-D8 350](https://www.tokopedia.com/indomakers/3d-printer-lead-screw-t8-2-d8-350mm-leadscrew-no-nut) + [anti-backlash nut, lead 2](https://www.tokopedia.com/lajarusteknik/t8-nut-block-lead-screw-anti-backlash-pitch-2mm-lead-2mm-1start) + [KFL08](https://www.tokopedia.com/lajarusteknik/pillow-block-bearing-kfl08-8mm-promo) + [5×8 coupler](https://www.tokopedia.com/lajarusteknik/flexible-coupling-5-x-8mm-d20-p25-coupler-aluminium-5mm-x-8mm) | ≈ Rp89k | Lajarus Teknik also sells the 2020 extrusion |
| P06 | [GT2 6 mm belt /m](https://www.tokopedia.com/centi-store/timing-belt-gt2-6mm-untuk-3d-printer-meteran-open-loop) + [20T 5 mm pulley](https://www.tokopedia.com/rajawali3d/gt2-timing-pulley-20-teeth-bore-5mm-belt-6mm) + [toothless idler 5 mm](https://www.tokopedia.com/3dinjakarta/gearless-idler-pulley-2gt-gt2-6mm-20t-20-bore-3mm-4mm-5mm-1736902733684836117) | ≈ Rp40k | |
| P08 | [metal ball caster](https://www.tokopedia.com/bustan/universal-ball-caster-metal-free-wheel-mata-sapi-for-smart-car-arduino) × 3 | Rp15k each | Must be < 27 mm tall (ask the seller); printed spacers to 42/27 mm |
| P10 | [KW11-3Z lever](https://www.tokopedia.com/best-ay/micro-limit-switch-kw11-3z-5a-250v-3-pin-saklar-terminal-gagang-no-nc) × 15 | Rp1.4k each | |
| P15 | [Pi camera FFC 50 cm](https://www.tokopedia.com/rajacell/kabel-camera-ffc-cable-untuk-kamera-raspberry-pi-3b-4b-15cm-30cm-50cm-15cm) | Rp10k | Pick the 50 cm variant |
| P19 | [INA226 module](https://www.tokopedia.com/solarperfect/ina226-i2c-bi-directional-dc-current-sensor-arus) + [2512 R010 shunt](https://www.tokopedia.com/wkh-elektronik/smd-2512-alloy-resistor-r010-0-010-ohm-10mr-accuracy-1-rshunt-10milir) | Rp22k + Rp3k | Product photos show **R100**: swap the shunt (hot air or two irons) |
| P21 | [XT30/XT60](https://www.tokopedia.com/teknoza/konektor-amass-xt30-xt60-xt90-male-female-xt30-27300), [JST-XH 230 pcs](https://www.tokopedia.com/easy-go-512/isi-230pcs-kit-housing-soket-kabel-listrik-jst-xh-2-54mm-konektor-kabel-2-pin-3-pin-4-pin-5-pin-terminal-1733880946592416840), [robot E-stop 1NC twist release](https://www.tokopedia.com/rnpstore/emergency-stop-push-lock-turn-to-release-22mm-1nc-xb2-es542) | — | Fuse holder, rocker switch, SS54, silicone wire: any local electronics shop |
| P37 | [USB-A → C 90° L-shape data cable](https://www.tokopedia.com/njatech/vivan-kabel-data-gaming-90-derajat-l-style-usb-a-to-c-fast-charging-15w-3a-casan-1734418008877597777) | Rp29k | 1 m (spec 0.3 m); check the plug exits up/away from J10/J11 |
| P38 | [Bosch 12 V 4-pin relay + ceramic socket](https://www.tokopedia.com/putrajayamotor-1/relay-bosch-original-kaki-4-12v-soket-relay-keramik-kaki-4) | Rp23k | + 1N4007 |
| P18, P27, P28, P29 | see the table below | | |

P23 (PCB components) is still to be itemised from `pcb/motion-board/fab/rbg3-motion-bom.csv`. P07 (bought wheels) is replaced by printed PETG hubs + TPU tires.

## 4. Candidates for the generic parts (first search)

| ID | Candidate | Price | Notes |
|---|---|---|---|
| P24 | [Delta DRL-24V120W1EN, Lyte II 120 W](https://www.tokopedia.com/mitra-otomasi/din-rail-power-supply-delta-drl-24v120w1en-lyte-ii-series-din-rail-120w-24v-input-1ph) | Rp622k ≈ 39 USD | DRC-24V100W1AZ (CliQ) is obsolete; its replacement is DRC-24V100W1RZ |
| P18 | [XY-3606 5 V 5 A](https://www.tokopedia.com/easyware-id/xy-3606-power-module-step-down-dc-to-dc-5a-24v-12v-to-5v-power-supply) | Rp22k | Pi + board |
| P18 | [MP2482/SY8205 5 A](https://www.tokopedia.com/cncstorebandung/dc-dc-mp2482-sy8205-5a-dc-step-down-module-7v-24v-to-5v-servo-power) | Rp19k | Servo rail. Must be adjustable to 6 V |
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
