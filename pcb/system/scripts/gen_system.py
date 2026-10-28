"""Generate the RackBotGen3 system wiring schematic (KiCad 10): robot harness, rack + spare station, and the
ESP32 rack-controller fallback. Plain text, no eeschema; safe to repeat (fixed UUIDs, so reruns give the same files).

  python3 pcb/system/scripts/gen_system.py

Blocks are modules or harness parts (custom symbols, embedded); fuses, diodes, switches, lamps and servos use the
stock KiCad symbols. As on the motion board, nets connect by name: every pin end carries a local label.
Source of truth: docs/spec/02-electrical.md (§1 robot power, §3.2 board connectors, §4 rack). The motion board's own
circuit is in pcb/motion-board/; here it is one block with its connectors.
"""

import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..")
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/"
PROJECT = "rbg3-system"
G = 2.54
NS = uuid.UUID("6f1c2b1e-0d5e-4a59-9b1e-7c3d2a5b8e10")


def uid(*key):
    return str(uuid.uuid5(NS, "/".join(str(k) for k in key)))


def fmt(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else f"{v:g}"


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ---------------------------------------------------------------- symbols

def sexp_block(text, start):
    depth, i = 0, start
    while True:
        c = text[i]
        if c == '"':
            i += 1
            while text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1


class Sym:
    """A library symbol: its embedded text and pin table {number: (name, x, y, angle)} in library coordinates."""

    def __init__(self, lib_id, text, pins):
        self.lib_id, self.text, self.pins = lib_id, text, pins


_stock_cache = {}


def stock(lib_id):
    if lib_id in _stock_cache:
        return _stock_cache[lib_id]
    lib, name = lib_id.split(":")
    t = open(STOCK + lib + ".kicad_sym").read()
    s = t.index('\n\t(symbol "%s"' % name) + 2
    body = sexp_block(t, s)
    assert "(extends" not in body, lib_id
    body = body.replace('(symbol "%s"' % name, '(symbol "%s"' % lib_id, 1)
    pins = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)', body):
        pb = sexp_block(body, m.start())
        num = re.search(r'\(number "([^"]*)"', pb).group(1)
        nm = re.search(r'\(name "([^"]*)"', pb).group(1)
        pins[num] = (nm, float(m.group(1)), float(m.group(2)), int(m.group(3)))
    _stock_cache[lib_id] = Sym(lib_id, body, pins)
    return _stock_cache[lib_id]


def text_effects(size=1.27, hide=False, justify=None):
    j = f" (justify {justify})" if justify else ""
    h = " (hide yes)" if hide else ""
    return f"(effects (font (size {size} {size})){j}{h})"


def block(name, left, right, width=25.4, ref="U", value="", desc="", show_numbers=False):
    """A rectangle with named pins. left/right: lists of pin names (None = a one-row gap). Pins are numbered in
    order, left side first. Pin rows are 2.54 apart; the symbol origin is the first row, horizontally centred."""
    lib_id = "sys:" + name
    rows = max(len(left), len(right))
    hw = width / 2
    top, bot = G, -rows * G
    pins, gfx = {}, []
    n = 0
    for side, names in (("L", left), ("R", right)):
        for i, pn in enumerate(names):
            if pn is None:
                continue
            n += 1
            y = -i * G
            x, ang = (-hw - G, 0) if side == "L" else (hw + G, 180)
            pins[str(n)] = (pn, x, y, ang)
            gfx.append(
                f'(pin passive line (at {fmt(x)} {fmt(y)} {ang}) (length {G}) '
                f'(name "{esc(pn)}" {text_effects()}) (number "{n}" {text_effects()}))')
    pn_hide = "" if show_numbers else " (hide yes)"
    body = (
        f'(symbol "{lib_id}" (pin_numbers{pn_hide}) (pin_names (offset 0.508)) (exclude_from_sim no) '
        f'(in_bom yes) (on_board yes)\n'
        f'(property "Reference" "{ref}" (at {fmt(-hw)} {fmt(top + 1.27)} 0) {text_effects(justify="left bottom")})\n'
        f'(property "Value" "{esc(value or name)}" (at {fmt(-hw)} {fmt(bot - 1.27)} 0) '
        f'{text_effects(justify="left top")})\n'
        f'(property "Footprint" "" (at 0 0 0) {text_effects(hide=True)})\n'
        f'(property "Datasheet" "" (at 0 0 0) {text_effects(hide=True)})\n'
        f'(property "Description" "{esc(desc)}" (at 0 0 0) {text_effects(hide=True)})\n'
        f'(symbol "{name}_0_1" (rectangle (start {fmt(-hw)} {fmt(top)}) (end {fmt(hw)} {fmt(bot)}) '
        f'(stroke (width 0.254) (type default)) (fill (type background))))\n'
        f'(symbol "{name}_1_1" ' + "\n".join(gfx) + "))")
    return Sym(lib_id, body, pins)


# ---------------------------------------------------------------- sheets

class Sheet:
    def __init__(self, fname, title, paper, comments, page_path):
        self.fname, self.title, self.paper, self.comments = fname, title, paper, comments
        self.uuid = uid(fname)
        self.page_path = page_path    # instance path of this sheet ("/root" or "/root/sheet")
        self.syms, self.items = {}, []
        self.nets = {}

    def place(self, sym, ref, x, y, rot=0, value=None, labels=None, nc=(), hide_value=False, fields=None):
        """Place sym at (x, y). labels: {pin name or number: net}. Pins listed in nc get a no-connect flag."""
        self.syms[sym.lib_id] = sym
        value = value if value is not None else sym.lib_id.split(":")[1]
        u = uid(self.fname, ref)
        lines = [f'(symbol (lib_id "{sym.lib_id}") (at {fmt(x)} {fmt(y)} {rot}) (unit 1) (body_style 1) '
                 f'(exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) (uuid "{u}")']
        # Reference/value: use the library positions for blocks, a simple offset for stock symbols.
        if sym.lib_id.startswith("sys:"):
            m = re.search(r'\(property "Reference" "[^"]*" \(at ([-\d.]+) ([-\d.]+)', sym.text)
            rx, ry = float(m.group(1)), float(m.group(2))
            m = re.search(r'\(property "Value" "[^"]*" \(at ([-\d.]+) ([-\d.]+)', sym.text)
            vx, vy = float(m.group(1)), float(m.group(2))
            lines.append(f'(property "Reference" "{ref}" (at {fmt(x + rx)} {fmt(y - ry)} 0) '
                         f'{text_effects(justify="left bottom")})')
            lines.append(f'(property "Value" "{esc(value)}" (at {fmt(x + vx)} {fmt(y - vy)} 0) '
                         f'{text_effects(justify="left top", hide=hide_value)})')
        else:
            # Stock symbols: reference and value to the right of the body, read horizontally. Field angles are
            # stored relative to the symbol, so a rotated symbol needs the opposite angle to stay horizontal.
            (rdx, rdy), (vdx, vdy) = fields or ((3.81, -1.27), (3.81, 1.27))
            fa = (360 - rot) % 180
            for name, txt, dx, dy, hide in (("Reference", ref, rdx, rdy, False),
                                            ("Value", esc(value), vdx, vdy, hide_value)):
                lines.append(f'(property "{name}" "{txt}" (at {fmt(x + dx)} {fmt(y + dy)} {fa}) '
                             f'{text_effects(justify="left", hide=hide)})')
        for f in ("Footprint", "Datasheet", "Description"):
            lines.append(f'(property "{f}" "" (at {fmt(x)} {fmt(y)} 0) {text_effects(hide=True)})')
        for num in sym.pins:
            lines.append(f'(pin "{num}" (uuid "{uid(self.fname, ref, "pin", num)}"))')
        lines.append(f'(instances (project "{PROJECT}" (path "{self.page_path}" (reference "{ref}") (unit 1))))')
        lines.append(")")
        self.items.append("\n".join(lines))

        by_name = {}
        for num, (nm, *_rest) in sym.pins.items():
            by_name.setdefault(nm, num)
        used = set()
        for key, net in (labels or {}).items():
            num = key if key in sym.pins else by_name[key]
            used.add(num)
            self.label(net, *self.pin_end(sym, num, x, y, rot))
        for key in nc:
            num = key if key in sym.pins else by_name[key]
            used.add(num)
            px, py, _ = self.pin_end(sym, num, x, y, rot)
            self.items.append(f'(no_connect (at {fmt(px)} {fmt(py)}) (uuid "{uid(self.fname, ref, "nc", num)}"))')
        missing = [sym.pins[n][0] or n for n in sym.pins if n not in used]
        assert not missing, f"{ref}: pins without a label or no-connect: {missing}"

    @staticmethod
    def pin_end(sym, num, x, y, rot):
        _nm, px, py, ang = sym.pins[num]
        r = rot % 360
        rx, ry = {0: (px, py), 90: (-py, px), 180: (-px, -py), 270: (py, -px)}[r]
        return x + rx, y - ry, (ang + 180 + r) % 360

    def label(self, net, x, y, ang):
        just = "left bottom" if ang in (0, 90) else "right bottom"
        n = self.nets.setdefault(net, 0)
        self.nets[net] = n + 1
        self.items.append(f'(label "{esc(net)}" (at {fmt(x)} {fmt(y)} {ang}) {text_effects(justify=just)} '
                          f'(uuid "{uid(self.fname, "label", net, n)}"))')

    def text(self, s, x, y, size=1.27, bold=False):
        b = " (bold yes)" if bold else ""
        self.items.append(f'(text "{esc(s)}" (exclude_from_sim no) (at {fmt(x)} {fmt(y)} 0) '
                          f'(effects (font (size {size} {size}){b}) (justify left top)) '
                          f'(uuid "{uid(self.fname, "text", x, y)}"))')

    def check_nets(self, allow_single=()):
        single = sorted(n for n, c in self.nets.items() if c < 2 and n not in allow_single)
        assert not single, f"{self.fname}: nets with only one label: {single}"

    def write(self, extra=""):
        tb = "".join(f'\n(comment {i + 1} "{esc(c)}")' for i, c in enumerate(self.comments))
        libs = "\n".join(s.text for s in self.syms.values())
        out = (f'(kicad_sch (version 20260306) (generator "rbg3_gen_system") (generator_version "10.0")\n'
               f'(uuid "{self.uuid}")\n(paper "{self.paper}")\n'
               f'(title_block (title "{esc(self.title)}") (date "2026-10-24") (rev "1") '
               f'(company "RackBotGen3 (Delta Cup 2026)"){tb})\n'
               f'(lib_symbols\n{libs}\n)\n' + "\n".join(self.items) + extra + "\n(embedded_fonts no)\n)\n")
        open(os.path.join(OUT, self.fname), "w").write(out)


# ---------------------------------------------------------------- robot

def robot(path):
    s = Sheet("robot.kicad_sch", "RBG3 system wiring: robot harness", "A2",
              ["Spec: docs/spec/02-electrical.md §1 (power), §3.2 (board connectors); parts: docs/parts.csv",
               "Nets connect by name (local labels); check block pin names on the bought modules"],
              path)

    pack = block("BATTERY_PACK", [], ["P+", "P−"], width=30.48, ref="BT",
                 desc="4S1P 18650 + 4S BMS (common port)")
    xt60 = block("XT60", ["pack+", "pack−"], ["harness+", "harness−"], width=20.32, ref="J",
                 desc="XT60 pair: female on the pack, male on the harness")
    s.place(pack, "BT1", 30.48, 50.8, value="4S1P 18650 3.5 Ah + 4S BMS ≥ 15 A (P20)",
            labels={"P+": "PACK+", "P−": "PACK−"})
    s.place(xt60, "J101", 78.74, 50.8, value="XT60 pair (P21)",
            labels={"pack+": "PACK+", "pack−": "PACK−", "harness+": "BAT+", "harness−": "GND"})

    fuse = stock("Device:Fuse")
    s.place(fuse, "F1", 116.84, 58.42, rot=90, value="7.5 A blade, inline holder", fields=((-3.81, -3.81), (-3.81, 3.81)),
            labels={"1": "BAT+", "2": "BAT_F+"})
    rocker = stock("Switch:SW_SPST")
    s.place(rocker, "SW1", 149.86, 58.42, value="Main switch, rocker 16 A", fields=((-3.81, -3.81), (-3.81, 3.81)),
            labels={"1": "BAT_F+", "2": "BAT_SW+"})
    ina = block("INA226", ["IN+", "IN−", "VBS", None, "VCC", "GND", "SDA", "SCL", "ALE"], [], width=22.86,
                ref="U", desc="INA226 module with a 10 mΩ (R010) shunt")
    s.place(ina, "U101", 195.58, 50.8, value="INA226 module, R010 shunt (P19)",
            labels={"IN+": "BAT_SW+", "IN−": "VBUS", "VBS": "VBUS", "VCC": "J16_3V3", "GND": "J16_GND",
                    "SDA": "I2C_SDA", "SCL": "I2C_SCL"}, nc=("ALE",))

    # E-stop relay: the button's NC contact feeds the coil; its contact makes VMOT.
    estop = block("ESTOP_1NO1NC", ["NC1", "NC2", None, "NO3", "NO4"], [], width=22.86, ref="SW",
                  desc="LA38-11ZS mushroom, twist release, 1 NO + 1 NC")
    s.place(estop, "SW2", 50.8, 106.68, value="Robot E-stop LA38-11ZS (P21)",
            labels={"NC1": "VBUS", "NC2": "K1_COIL+", "NO3": "J13_GND", "NO4": "AUX_IN"})
    relay = block("RELAY_AUTO_4P", ["86(coil+)", "85(coil−)", None, "30(COM)", "87(NO)"], [], width=25.4,
                  ref="K", desc="12 V automotive relay SPST-NO 30/40 A")
    s.place(relay, "K1", 101.6, 106.68, value="12 V automotive relay 30/40 A (P38)",
            labels={"86(coil+)": "K1_COIL+", "85(coil−)": "GND", "30(COM)": "VBUS", "87(NO)": "VMOT"})
    diode = stock("Device:D")
    s.place(diode, "D101", 134.62, 114.3, value="1N4007 across the coil", fields=((-3.81, -3.81), (-3.81, 3.81)),
            labels={"1": "K1_COIL+", "2": "GND"})

    # Bucks (off-board modules). OUT− is the same node as IN− inside a non-isolated buck; the separate net names
    # show where each ground wire runs (02 §3.3 harness rule).
    buck = block("BUCK", ["IN+", "IN−"], ["OUT+", "OUT−"], width=20.32, ref="U", desc="DC-DC buck module")
    s.place(buck, "U102", 195.58, 106.68, value="Buck 5.15 V / 5 A (P18)",
            labels={"IN+": "VBUS", "IN−": "GND", "OUT+": "+5V", "OUT−": "GND_5V"})
    s.place(buck, "U103", 195.58, 132.08, value="Buck 5.8 V / 3 A, servos (P18)",
            labels={"IN+": "VMOT", "IN−": "GND", "OUT+": "+6V_SERVO", "OUT−": "GND_6V"})

    # Charging from the spare-station dock.
    pads = block("ROBOT_DOCK_PADS", [], ["+", "−"], width=22.86, ref="J",
                 desc="Copper pads on the robot, mate with the spare-station dock contacts")
    s.place(pads, "J102", 30.48, 167.64, value="Robot charging pads (P30)",
            labels={"+": "DOCK_PAD+", "−": "DOCK_PAD−"})
    schottky = stock("Device:D_Schottky")
    s.place(schottky, "D102", 81.28, 167.64, rot=180, value="SS54", fields=((-3.81, -3.81), (-3.81, 3.81)), labels={"1": "CHG_IN+", "2": "DOCK_PAD+"})
    chg = block("CHARGER_CCCV", ["IN+", "IN−"], ["OUT+", "OUT−"], width=22.86, ref="U",
                desc="XL4015-type CC/CV buck, 16.8 V / 1.5 A")
    s.place(chg, "U104", 129.54, 167.64, value="CC/CV charger 16.8 V / 1.5 A (P18)",
            labels={"IN+": "CHG_IN+", "IN−": "DOCK_PAD−", "OUT+": "VBUS", "OUT−": "GND"})

    # Compute.
    pi = block("RPI3", ["5V(µUSB)", "GND(µUSB)"], ["USB-A", "CSI"], width=30.48, ref="U",
               desc="Raspberry Pi 3B/3B+")
    s.place(pi, "U105", 251.46, 106.68, value="Raspberry Pi 3B+ (P12)",
            labels={"5V(µUSB)": "+5V", "GND(µUSB)": "GND_5V", "USB-A": "USB_PI_ESP32",
                    "CSI": "CSI_CAM"})
    cam = block("CAMERA", ["CSI"], [], width=20.32, ref="U", desc="IMX708 120° camera board")
    s.place(cam, "U106", 309.88, 106.68, value="IMX708 wide camera (P13)", labels={"CSI": "CSI_CAM"})

    # Motion board: one block with every connector (pin names as on the silkscreen).
    left = ["J1:GND", "J1:VMOT", None, "J2:+5V", "J2:GND", None, "J3:+6V", "J3:GND", None,
            "J16:3V3", "J16:G", "J16:SDA", "J16:SCL", None, "J17:5V", "J17:DI", "J17:G", None,
            "J18:DOCK_V+", "J18:NC", None, "J19:5V", "J19:BZ−", None, "USB-C(DevKit)", None,
            "J14:G", "J14:+", "J14:S", None, "J15:G", "J15:+", "J15:S"]
    right = []
    for j, ax in (("J4", "L"), ("J5", "R"), ("J6", "Z"), ("J7", "Y")):
        right += [f"{j}:2B", f"{j}:2A", f"{j}:1A", f"{j}:1B", None]
    for j in ("J8", "J9", "J10", "J11", "J12", "J13"):
        right += [f"{j}:G", f"{j}:S", f"{j}:3V3", None]
    board = block("RBG3_MOTION", left, right[:-1], width=40.64, ref="A",
                  desc="RBG3-MOTION v1 motion board (pcb/motion-board)")
    lab = {"J1:GND": "GND", "J1:VMOT": "VMOT", "J2:+5V": "+5V", "J2:GND": "GND_5V", "J3:+6V": "+6V_SERVO",
           "J3:GND": "GND_6V", "J16:3V3": "J16_3V3", "J16:G": "J16_GND", "J16:SDA": "I2C_SDA",
           "J16:SCL": "I2C_SCL", "J17:5V": "LED_5V", "J17:DI": "LED_DIN", "J17:G": "LED_GND",
           "J18:DOCK_V+": "DOCK_PAD+", "J19:5V": "BUZ_5V", "J19:BZ−": "BUZ_N", "USB-C(DevKit)": "USB_PI_ESP32",
           "J14:G": "SRV_A_G", "J14:+": "SRV_A_6V", "J14:S": "SRV_A_SIG",
           "J15:G": "SRV_B_G", "J15:+": "SRV_B_6V", "J15:S": "SRV_B_SIG"}
    for j, ax in (("J4", "L"), ("J5", "R"), ("J6", "Z"), ("J7", "Y")):
        for p in ("2B", "2A", "1A", "1B"):
            lab[f"{j}:{p}"] = f"MOT_{ax}_{p}"
    sw_nets = {"J8": "Z_HOME", "J9": "Y_HOME", "J10": "NOSE", "J11": "SLOT_A", "J12": "SLOT_B", "J13": "AUX_IN"}
    for j, net in sw_nets.items():
        lab[f"{j}:G"] = f"{j}_GND"
        lab[f"{j}:S"] = net
    nc = ["J18:NC"] + [f"{j}:3V3" for j in sw_nets]
    s.place(board, "A1", 401.32, 50.8, value="RBG3-MOTION v1 (ESP32-S3 + 4× TMC2209), pcb/motion-board",
            labels=lab, nc=nc)

    # Loads on the board connectors.
    motor = block("STEPPER_NEMA17", ["1A", "1B", "2A", "2B"], [], width=20.32, ref="M",
                  desc="NEMA17 bipolar stepper; coil 1 = 1A/1B, coil 2 = 2A/2B")
    for i, (ax, what) in enumerate((("L", "drive left"), ("R", "drive right"), ("Z", "Z lift"),
                                    ("Y", "Y extractor"))):
        s.place(motor, f"M{i + 1}", 500.38, 50.8 + i * 22.86, value=f"NEMA17 {what} (P01)",
                labels={p: f"MOT_{ax}_{p}" for p in ("1A", "1B", "2A", "2B")})
    kw = block("KW11_3Z", ["COM", "NO", "NC"], [], width=17.78, ref="S", desc="KW11-3Z lever microswitch")
    sws = (("J8", "Z_HOME", "Z home (NC)", "NC"), ("J9", "Y_HOME", "Y home (NC)", "NC"),
           ("J10", "NOSE", "nose dock (NO)", "NO"), ("J11", "SLOT_A", "tray slot A (NO)", "NO"),
           ("J12", "SLOT_B", "tray slot B (NO)", "NO"))
    for i, (j, net, what, contact) in enumerate(sws):
        other = "NO" if contact == "NC" else "NC"
        s.place(kw, f"S{i + 1}", 500.38, 147.32 + i * 17.78, value=f"KW11-3Z {what} (P10)",
                labels={"COM": f"{j}_GND", contact: net}, nc=(other,))
    servo = stock("Motor:Motor_Servo")
    s.place(servo, "M5", 345.44, 165.1, value="MG90S finger A (P09)", fields=((10.16, -5.08), (7.62, 6.35)),
            labels={"1": "SRV_A_SIG", "2": "SRV_A_6V", "3": "SRV_A_G"})
    s.place(servo, "M6", 345.44, 187.96, value="MG90S finger B (P09)", fields=((10.16, -5.08), (7.62, 6.35)),
            labels={"1": "SRV_B_SIG", "2": "SRV_B_6V", "3": "SRV_B_G"})
    led = block("WS2812_LED", ["5V", "DIN", "GND"], [], width=17.78, ref="D", desc="WS2812 status LED on a lead")
    s.place(led, "D103", 345.44, 129.54, value="WS2812 status LED", labels={"5V": "LED_5V", "DIN": "LED_DIN",
                                                                          "GND": "LED_GND"})
    bz = stock("Device:Buzzer")
    s.place(bz, "BZ1", 345.44, 147.32, value="Active buzzer 5 V", fields=((5.08, -1.27), (5.08, 1.27)), labels={"1": "BUZ_5V", "2": "BUZ_N"})

    s.text("Robot harness. Power path: pack → XT60 → F1 7.5 A → SW1 → INA226 shunt → VBUS (12–16.8 V).\n"
           "VBUS → E-stop NC → K1 coil (K1 makes VMOT) → VMOT → board J1 (XT30) and the servo buck.\n"
           "VBUS → 5 V buck → Pi (micro-USB pigtail) and board J2. The ESP32 is powered over USB from the Pi.\n"
           "Charging: dock pads → SS54 → CC/CV charger → VBUS (charges the pack through the INA226, current reads −).\n"
           "DOCK_PAD− goes ONLY to the charger IN−, never to GND: the charger senses current between IN− and OUT−.",
           20.32, 241.3, size=1.6)
    s.text("Wires (02 §1): VBUS/VMOT and pack 18 AWG silicone red/black (tag VMOT); dock pads → charger 18 AWG;\n"
           "5 V and 6 V buck outputs 20 AWG; motors 22–24 AWG JST-XH 4p; switches, E-stop NO, DOCK_V 26 AWG JST-XH.\n"
           "Connectors: XT60 at the pack, XT30 pigtail to J1, 5.08 screw terminals J2/J3, JST-XH J4–J13 and J16–J19.\n"
           "Ground rule (02 §3.3): GND_5V and GND_6V run from each buck's OUT− to J2/J3, not back to the pack;\n"
           "keep the J1 GND lead short and thick. GND, GND_5V and GND_6V are one node (inside the bucks and on A1).\n"
           "J8–J13: switch COM → G, contact → S; the 3V3 pin is spare. Home switches use NC (open = home or broken wire).\n"
           "Polarity: wire red = +, black = −; meter every lead before the first plug-in (A1 README bring-up).",
           20.32, 264.16, size=1.6)
    s.check_nets(allow_single=())
    return s


# ---------------------------------------------------------------- rack + spare station

def rack(path):
    s = Sheet("rack.kicad_sch", "RBG3 system wiring: rack and spare station", "A3",
              ["Spec: docs/spec/02-electrical.md §4 (rack), §5 (safety); 03 §4 (Modbus); 01 §5 (stations)",
               "U201 terminals are the PLC's; the ESP32 fallback (sheet 4) exposes the same functions"], path)

    mains = block("MAINS_CORD", [], ["L", "N", "PE"], width=20.32, ref="J", desc="Mains cord 220 V / 50 Hz")
    s.place(mains, "J201", 25.4, 38.1, value="Mains 220 V cord + plug", labels={"L": "AC_L", "N": "AC_N",
                                                                               "PE": "PE"})
    psu = block("PSU_24V", ["L", "N", "PE"], ["+V", "−V"], width=22.86, ref="PS", desc="Delta DRL-24V120W1EN")
    s.place(psu, "PS201", 71.12, 38.1, value="Delta DRL-24V120W1EN 24 V 5 A (P24)",
            labels={"L": "AC_L", "N": "AC_N", "PE": "PE", "+V": "+24V", "−V": "0V"})
    s.text("PE: also bond the aluminium rack frame to PE.", 20.32, 55.88)

    ctl = block("RACK_CONTROLLER",
                ["24V", "0V", "S/S", None, "X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7"],
                ["UP", "ZP", None, "Y0", "Y1", "Y2", "Y3", None, "LAN"], width=30.48, ref="U",
                desc="Delta DVP-12SE11T terminals (or the ESP32 fallback, sheet 4)")
    s.place(ctl, "U201", 157.48, 38.1, value="Rack controller: Delta DVP-12SE11T (P25) or ESP32 fallback (P40)",
            labels={"24V": "+24V", "0V": "0V", "S/S": "0V", "X0": "X0", "X1": "X1", "X2": "X2", "X3": "X3",
                    "X4": "X4", "X5": "X5", "X6": "X6", "X7": "X7", "UP": "+24V", "ZP": "0V",
                    "Y0": "Y0", "Y1": "Y1", "Y2": "Y2", "Y3": "Y3"}, nc=("LAN",))
    s.text("LAN: only with the PLC (Wi-Fi client bridge to\nthe Pi AP RACKBOT, 02 §4.3). The ESP32 uses Wi-Fi.",
           190.5, 66.04)

    kw = block("KW11_3Z", ["COM", "NO", "NC"], [], width=17.78, ref="S", desc="KW11-3Z lever microswitch")
    for i in range(4):
        s.place(kw, f"S{201 + i}", 30.48, 81.28 + i * 17.78, value=f"KW11-3Z bay {i + 1} caddy present (P10)",
                labels={"COM": "+24V", "NO": f"X{i}"}, nc=("NC",))

    estop = block("ESTOP_2NC", ["NC-A1", "NC-A2", None, "NC-B1", "NC-B2"], [], width=20.32, ref="SW",
                  desc="Rack E-stop, mushroom, 2 × NC")
    s.place(estop, "SW201", 45.72, 160.02, value="Rack E-stop 2 × NC (P28)",
            labels={"NC-A1": "+24V", "NC-A2": "X5", "NC-B1": "+24V", "NC-B2": "DOCK_RLY_24V"})

    rly = block("RELAY_MODULE_24V", ["DC+", "DC−", "IN"], ["COM", "NO", "NC"], width=22.86, ref="K",
                desc="24 V relay module (Songle SRD), low-level trigger")
    s.place(rly, "K201", 106.68, 101.6, value="24 V relay module, low-level trigger (P26)",
            labels={"DC+": "DOCK_RLY_24V", "DC−": "0V", "IN": "Y0", "COM": "+24V_F", "NO": "DOCK+"}, nc=("NC",))
    fuse = stock("Device:Fuse")
    s.place(fuse, "F201", 106.68, 129.54, rot=90, value="3.15 A slow-blow, UK5-HESI", fields=((-3.81, -3.81), (-3.81, 3.81)), labels={"1": "+24V", "2": "+24V_F"})

    lamp = stock("Device:Lamp")
    for i, (col, y) in enumerate((("GREEN", "Y1"), ("YELLOW", "Y2"), ("RED", "Y3"))):
        s.place(lamp, f"H{201 + i}", 233.68 + i * 33.02, 109.22, value=f"{col} 24 V 22 mm (P27)",
                labels={"2": "+24V", "1": y})

    # Station cables: rack side on the left, spare-station side on the right.
    w1 = block("CABLE_4C", ["+24V", "X4", "X6", "X7"], ["+24V", "X4", "X6", "X7"], width=30.48, ref="W",
               desc="4-core signal cable, about 1.5 m")
    s.place(w1, "W201", 190.5, 147.32, value="4-core signal cable ≈ 1.5 m (P30)",
            labels={"1": "+24V", "2": "X4", "3": "X6", "4": "X7",
                    "5": "STN_24V", "6": "STN_X4", "7": "STN_X6", "8": "STN_X7"})
    w2 = block("CABLE_2C", ["DOCK+", "DOCK−"], ["DOCK+", "DOCK−"], width=30.48, ref="W",
               desc="2-core 0.75 mm² dock power lead, about 1.5 m")
    s.place(w2, "W202", 190.5, 175.26, value="2-core 0.75 mm² dock lead ≈ 1.5 m (P30)",
            labels={"1": "DOCK+", "2": "0V", "3": "STN_DOCK+", "4": "STN_DOCK−"})

    for i, (net, what) in enumerate((("STN_X4", "dock: robot home (X4)"), ("STN_X6", "S1 GOOD present (X6)"),
                                     ("STN_X7", "S2 RMA present (X7)"))):
        s.place(kw, f"S{205 + i}", 304.8, 139.7 + i * 17.78, value=f"KW11-3Z {what} (P10)",
                labels={"COM": "STN_24V", "NO": net}, nc=("NC",))
    dock = block("STATION_DOCK_CONTACTS", ["+(right)", "−(left)"], [], width=27.94, ref="J",
                 desc="Spring contacts on the spare-station dock stop face, 80 mm apart")
    s.place(dock, "J202", 304.8, 198.12, value="Dock contacts, spare station (P30)",
            labels={"+(right)": "STN_DOCK+", "−(left)": "STN_DOCK−"})

    s.text("Rack DIN rail: PSU, U201, K201, F201, terminal blocks for +24V / 0V. Spare station: S205–S207 and J202.\n"
           "Inputs: switches connect +24V to Xn, S/S to 0V (sourcing). Outputs Y0–Y3 sink (NPN): lamps and K201 IN\n"
           "go between +24V and Yn. UP = +24V, ZP = 0V power the PLC's transistor outputs.\n"
           "Dock power: K201 closes only while Y0 = M0 AND X4 AND X5 AND watchdog OK (ladder, 03 §4). The E-stop's\n"
           "second NC contact feeds K201's DC+, so a pressed E-stop drops the relay in hardware.\n"
           "J202 mates with the robot's charging pads (robot sheet J102): + on the right, − on the left, viewed from\n"
           "the robot. 24 V reaches the pads only while the robot is docked and X4 is closed.\n"
           "The rack's own dock has no switch and no contacts (01 §4): the robot's NOSE switch confirms docking there.",
           20.32, 223.52, size=1.6)
    s.check_nets()
    return s


# ---------------------------------------------------------------- ESP32 rack-controller fallback

def rack_esp32(path):
    s = Sheet("rack-esp32.kicad_sch", "RBG3 system wiring: ESP32 rack controller (PLC fallback)", "A3",
              ["Spec: docs/spec/02-electrical.md §4.4; parts: P40",
               "GPIO choice is a proposal: confirm it when the rack firmware is written"], path)
    buck = block("BUCK", ["IN+", "IN−"], ["OUT+", "OUT−"], width=20.32, ref="U", desc="DC-DC buck module")
    s.place(buck, "U301", 30.48, 38.1, value="Buck 24 → 5 V (P40)",
            labels={"IN+": "+24V", "IN−": "0V", "OUT+": "+5V", "OUT−": "0V"})
    esp = block("ESP32_DEVKIT_V1",
                ["VIN(5V)", "GND", "3V3", None, "GPIO32", "GPIO33", "GPIO25", "GPIO26", "GPIO27", "GPIO14",
                 "GPIO13", "GPIO4"],
                ["GPIO16", "GPIO17", "GPIO18", "GPIO19"], width=30.48, ref="U",
                desc="ESP32 DevKit V1 (WROOM-32), 30 pins")
    s.place(esp, "U302", 177.8, 38.1, value="ESP32 DevKit V1 WROOM-32 (P40)",
            labels={"VIN(5V)": "+5V", "GND": "0V", "3V3": "+3V3",
                    "GPIO32": "IN_X0", "GPIO33": "IN_X1", "GPIO25": "IN_X2", "GPIO26": "IN_X3",
                    "GPIO27": "IN_X4", "GPIO14": "IN_X5", "GPIO13": "IN_X6", "GPIO4": "IN_X7",
                    "GPIO16": "TRIG_Y0", "GPIO17": "TRIG_Y1", "GPIO18": "TRIG_Y2", "GPIO19": "TRIG_Y3"})
    opto = block("OPTO_IN_8CH",
                 ["IN1", "IN2", "IN3", "IN4", "IN5", "IN6", "IN7", "IN8", None, "COM"],
                 ["OUT1", "OUT2", "OUT3", "OUT4", "OUT5", "OUT6", "OUT7", "OUT8", None, "VCC", "GND"],
                 width=25.4, ref="U", desc="8-channel 24 V → 3.3 V optocoupler input board")
    lab = {f"IN{i + 1}": f"X{i}" for i in range(8)}
    lab.update({f"OUT{i + 1}": f"IN_X{i}" for i in range(8)})
    lab.update({"COM": "0V", "VCC": "+3V3", "GND": "0V"})
    s.place(opto, "U303", 91.44, 81.28, value="8-ch 24 V opto input board (P40)", labels=lab)
    mos = block("MOSFET_2CH", ["DC+", "DC−", None, "TRIG1", "TRIG2", "GND"], ["OUT1−", "OUT2−"],
                width=22.86, ref="U", desc="Dual MOSFET module D4184, low-side, 3.3 V trigger")
    s.place(mos, "U304", 254.0, 81.28, value="Dual MOSFET D4184 (P40): Y0, Y1",
            labels={"DC+": "+24V", "DC−": "0V", "TRIG1": "TRIG_Y0", "TRIG2": "TRIG_Y1", "GND": "0V",
                    "OUT1−": "Y0", "OUT2−": "Y1"})
    s.place(mos, "U305", 254.0, 116.84, value="Dual MOSFET D4184 (P40): Y2, Y3",
            labels={"DC+": "+24V", "DC−": "0V", "TRIG1": "TRIG_Y2", "TRIG2": "TRIG_Y3", "GND": "0V",
                    "OUT1−": "Y2", "OUT2−": "Y3"})
    term = block("RACK_TERMINALS",
                 ["+24V", "0V", None, "X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7"],
                 ["Y0", "Y1", "Y2", "Y3"], width=27.94, ref="X",
                 desc="Terminal-block row with the PLC's terminal names (rack sheet U201)")
    lab = {n: n for n in ["+24V", "0V"] + [f"X{i}" for i in range(8)] + [f"Y{i}" for i in range(4)]}
    s.place(term, "X301", 45.72, 132.08, value="Terminal row = rack sheet U201 terminals", labels=lab)

    s.text("Replaces U201 on the rack sheet: the wires that went to the PLC's X0–X7, Y0–Y3, 24V and 0V land on X301.\n"
           "Inputs: opto IN1–IN8 take the +24 V switch signals with COM to 0V; the opto outputs pull the GPIOs low\n"
           "when an input is on (use INPUT_PULLUP if the board has no pull-ups; check its jumper/polarity).\n"
           "Outputs: the D4184 modules sink like the PLC's NPN outputs, so lamps and the dock relay module (low-level\n"
           "trigger) keep their +24V common wiring. GPIO16–19 drive the triggers (3.3 V logic).\n"
           "Proposed pins avoid the ESP32 strapping pins 0, 2, 5, 12, 15 and the flash pins 6–11; GPIO34–39 are left\n"
           "free (input-only, no pull-ups). The firmware exposes the same Modbus TCP map as the PLC (03 §4) over Wi-Fi.\n"
           "Module pin names vary by vendor: check the bought boards before wiring.",
           20.32, 172.72, size=1.6)
    s.check_nets()
    return s


# ---------------------------------------------------------------- root

SHEETS = []


def main():
    root_uuid = uid("rbg3-system.kicad_sch")
    pages = [("Robot harness", "robot.kicad_sch", robot), ("Rack and spare station", "rack.kicad_sch", rack),
             ("ESP32 rack controller (PLC fallback)", "rack-esp32.kicad_sch", rack_esp32)]
    sheet_blocks = []
    for i, (title, fname, fn) in enumerate(pages):
        su = uid("sheet", fname)
        sh = fn(f"/{root_uuid}/{su}")
        sh.write()
        SHEETS.append(sh)
        x, y, w, h = 30.48 + i * 76.2, 101.6, 66.04, 25.4
        sheet_blocks.append(
            f'(sheet (at {fmt(x)} {fmt(y)}) (size {fmt(w)} {fmt(h)}) (exclude_from_sim no) (in_bom yes) '
            f'(on_board yes) (dnp no) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) '
            f'(fill (color 0 0 0 0.0000)) (uuid "{su}")\n'
            f'(property "Sheetname" "{esc(title)}" (at {fmt(x)} {fmt(y - 0.7)} 0) '
            f'{text_effects(justify="left bottom")})\n'
            f'(property "Sheetfile" "{fname}" (at {fmt(x)} {fmt(y + h + 0.6)} 0) '
            f'{text_effects(justify="left top")})\n'
            f'(instances (project "{PROJECT}" (path "/{root_uuid}" (page "{i + 2}")))))')

    root = Sheet("rbg3-system.kicad_sch", "RBG3 system wiring: overview", "A4",
                 ["Generated by pcb/system/scripts/gen_system.py; edit the script, not these files",
                  "Board-level circuit: pcb/motion-board/rbg3-motion.kicad_sch"], "/" + root_uuid)
    root.uuid = root_uuid
    root.text("RackBotGen3 (Corvin) system wiring", 30.48, 30.48, size=3, bold=True)
    root.text("Sheet 2: robot harness (battery, fuse, switch, INA226, E-stop relay, bucks, charger, Pi, motion\n"
              "board connectors, motors, switches, servos, LED, buzzer).\n"
              "Sheet 3: rack and spare station (mains, 24 V PSU, rack controller terminals, bay switches, E-stop,\n"
              "dock relay, lamps, station cables, dock contacts and station switches).\n"
              "Sheet 4: ESP32 rack controller, the PLC fallback (P40), wired to the same terminal names.\n\n"
              "The two sides meet only at the spare-station dock: robot pads J102 ↔ station contacts J202\n"
              "(24 V charging, switched by the rack's dock relay), and over Wi-Fi (Pi AP RACKBOT ↔ rack controller).",
              30.48, 45.72, size=1.8)
    extra = "\n" + "\n".join(sheet_blocks) + f'\n(sheet_instances (path "/" (page "1")))'
    root.write(extra)

    # The custom blocks also go into a project library, so ERC finds them and they can be reused in eeschema.
    blocks = {}
    for sh in SHEETS:
        blocks.update({k: v for k, v in sh.syms.items() if k.startswith("sys:")})
    lib = "\n".join(v.text.replace(f'(symbol "{k}"', f'(symbol "{k[4:]}"', 1) for k, v in sorted(blocks.items()))
    open(os.path.join(OUT, "rbg3-system.kicad_sym"), "w").write(
        f'(kicad_symbol_lib (version 20251024) (generator "rbg3_gen_system") (generator_version "10.0")\n{lib}\n)\n')
    open(os.path.join(OUT, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "sys")(type "KiCad")(uri "${KIPRJMOD}/rbg3-system.kicad_sym")'
        '(options "")(descr "RBG3 system wiring blocks (generated)"))\n)\n')

    pro = ('{\n  "meta": {"filename": "rbg3-system.kicad_pro", "version": 3},\n'
           f'  "sheets": [["{root_uuid}", "Root"]' +
           "".join(f', ["{uid("sheet", f)}", "{t}"]' for t, f, _ in pages) + "]\n}\n")
    open(os.path.join(OUT, "rbg3-system.kicad_pro"), "w").write(pro)
    print("wrote", ", ".join(["rbg3-system.kicad_sch"] + [f for _, f, _ in pages]))


if __name__ == "__main__":
    main()
