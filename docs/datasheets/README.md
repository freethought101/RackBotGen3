# Datasheets

Spec values checked against these files: [CROSSCHECK.md](CROSSCHECK.md).

| File | Part | Source |
|---|---|---|
| P09_mg90s.pdf | P09 MG90S servo | electronicoscaldas.com mirror (TowerPro) |
| P12_raspberry-pi-3b-plus_brief.pdf | P12 Raspberry Pi 3B+ | datasheets.raspberrypi.com |
| P13_camera-module-3_brief.pdf | P13 Camera Module 3 | datasheets.raspberrypi.com |
| P16_esp32-s3_datasheet.pdf | P16 ESP32-S3 | espressif.com |
| P16_esp32-s3-devkitc-1_schematic.pdf | P16 DevKitC-1 v1.1 schematic | dl.espressif.com |
| P17_tmc2209.pdf | P17 TMC2209 (U2-U5) | analog.com / DigiKey mirror (if present) |
| P19_ina226.pdf | P19 INA226 | ti.com |
| PCB_mmbt3904.pdf | Q1 MMBT3904 | diodes.com |
| PCB_1n4148w.pdf | D2 1N4148W | diodes.com |
| PCB_1n4007.pdf | P38 flyback diode 1N4007 | diodes.com |
| PCB_ws2812b.pdf | WS2812B | adafruit mirror |
| P18_xl4015.pdf | P18 XL4015E1 buck chip (5 A / 36 V, charger) | LCSC (found via browser) |
| P24_delta-drp024v060w1az.pdf | P24 Delta CliQ DRP-024V060W1AZ (earlier example model; superseded by the DRL-24V120W1EN sheet below) | deltapsu.com |
| P25_delta-dvp-se_instruction-sheet.pdf | P25 Delta DVP-SE series PLC instruction sheet | deltaacdrives.com |
| PCB_xt30pw-m.pdf | J1 XT30PW-M | AMASS via szlcsc.com |
| PCB_jst-xh.pdf | J4-J19 JST XH series | jst-mfg.com |
| PCB_mkds-1.5-2-5.08.pdf | J2/J3 Phoenix MKDS 1,5/2-5,08 | DigiKey mirror |
| PCB_smbj18a_vishay.pdf | D1 SMBJ18A (Vishay SMBJ series) | vishay.com |
| PCB_smbj18a_bourns.pdf | D1 SMBJ18A (Bourns SMBJ series) | bourns.com |
| PCB_ss54_vishay-SSC54-equivalent.pdf | D? SS54 stand-in: Vishay SSC54 (5 A / 40 V Schottky, SMC); not the exact SS54 sheet | vishay.com |
| P20_samsung-inr18650-35e.pdf | P20 Samsung INR18650-35E cell | rapidonline.com |
| P20_lg-inr18650-mj1.pdf | P20 LG INR18650 MJ1 cell (older revision) | piekarz.pl mirror |
| P18_mp2482.pdf | P18 MP2482 5 A buck chip (6 V servo rail module) | utu.fi mirror of the MPS datasheet |
| P17_mks-tmc2209-v2.0_schematic.pdf, P17_mks-tmc2209-v2.0_size-pin.png | P17 MKS TMC2209 V2.0 module schematic + size/pin drawing | github.com/makerbase-mks/MKS-StepStick-Driver |
| P01_jkongmotor_stepper-catalog-2024.pdf | P01 JK42HS40-1704 (full Jkongmotor stepper catalog, scanned images; model is in the spec table on PDF pages 32-33) | jkongmotor.com download center |
| P18_sy8205.pdf | P18 SY8205FCC buck chip | LCSC (found via browser) |
| PCB_smbj18a_littelfuse.pdf | D1 SMBJ18A, Littelfuse | LCSC (found via browser) |
| PCB_ss54_mdd.pdf | SS54, MDD (exact part) | LCSC (found via browser) |
| P38_bosch-relays-aftermarket.pdf | P38 Bosch relays overview (mini relay family, not a model-specific sheet) | boschaftermarket.com |
| P12_raspberry-pi-3b-plus_mechanical-drawing.pdf, P12_raspberry-pi-3b-plus_reduced-schematics.pdf | P12 Pi 3B+ mechanical drawing + reduced schematics | datasheets.raspberrypi.com |
| P13_camera-module-3_sensor-assembly-brief.pdf | P13 Camera Module 3 sensor assembly brief (IMX708) | pip.raspberrypi.com |
| P15_csi-camera-cable-200mm-drawing.pdf | P15 standard CSI cable reference drawing (200 mm version; yours is 500 mm) | pip.raspberrypi.com |
| P25_delta-dvp-series-plc-catalog.pdf, P25_delta-dvp12se-dimensions.pdf | P25 Delta DVP PLC catalogue + DVP12SE dimensions | deltaacdrives.com |
| P24_delta-drl-24v120w1en.pdf | P24 Delta LYTE II DRL-120W series (the chosen DRL-24V120W1EN: 24 V 5 A, 123.6 × 30 × 116.8 mm); Rev. 02, June 2021 | piekarz.pl mirror (deltapsu.com download needs a captcha) |
| P26_songle-srd-relay.pdf | P26 Songle SRD series relay (SRD-24VDC-SL-C is the usual relay on 24 V relay modules; check the marking on the module you get) | LCSC C15840 |
| P21_amass-xt60h.pdf | P21 Amass XT60H connector | LCSC C5334533 |

## Product pages (no PDF)
- P31 GL.iNet GL-MT300N-V2 router: specs on [docs.gl-inet.com](https://docs.gl-inet.com/router/en/3/specification/gl-mt300n-v2/) (5 V / 2 A in, < 2.75 W, 2 × 10/100 Ethernet, 58 × 58 × 25 mm).
- P04 OpenBuilds mini V-wheel: dimensions on [Rat Rig](https://ratrig.com/products/mini-v-wheel-kit) (Ø ≈ 15.2 mm, 8.8 mm thick); OpenBuilds publishes CAD, not a PDF.

## Generic (no manufacturer datasheet; buy by the listing in docs/shopping-list.md)
- P21: LA38-11ZS E-stop (sold by many brands; listings give 10 A, Ui 440 V, 1 NO + 1 NC); 16 A rocker switch; blade fuse holder; silicone wire.
- P26/P28/P27: rack E-stop box, UK5N-style DIN terminal blocks, DIN rail, tower light.
- P20: 4S 30 A BMS board and pure nickel strip.
- P19: 2512 R010 shunt resistor.
- P23: buzzer, WS2812 board (the WS2812B chip sheet is saved), 0805 passives, electrolytics, StepStick sockets and pin headers.
- P04–P08: V-wheels, T8 lead screw and nut, KFL08, GT2 belt and pulleys, W420 caster.
- P02/P03 extrusion, P11 fasteners, P14 microSD, P37 USB cable, P32–P36 filament, ballast, labels and mat.

## Not found
- XY-3606 buck module (P18): sold with shop pages only; the module has no manufacturer datasheet.
- KW11-3Z (P10): generic part, no manufacturer datasheet.
- BTT TMC2209 V1.3 board schematic (P17 now names the MKS module instead).
- Delta DVP-12SE11T programming manual (the SE instruction sheet, catalogue and dimensions are saved).
