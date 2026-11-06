"""Build docs/budget/rig-purchases.xlsx: every paid order for the table rig, checked against its receipt.

Data is typed in below from the receipts (INV = orders, IT = line items, NEED = what the rig needs, TODO = still to
buy). Edit the lists, then run from the repo root:

    uvx --with openpyxl python docs/budget/build_rig_purchases.py docs/budget/rig-purchases.xlsx

It prints a cross-check (totals vs receipts, items vs order subtotals, shortfalls). Formulas are not pre-calculated;
Excel/Numbers compute them on open.
"""

import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter as L

OUT = sys.argv[1]
F = "Arial"
BLUE = Font(name=F, color="0000FF"); BLK = Font(name=F); BOLD = Font(name=F, bold=True)
GREEN = Font(name=F, color="008000"); HEAD = Font(name=F, bold=True, color="FFFFFF")
HFILL = PatternFill("solid", fgColor="1F3A5F"); TFILL = PatternFill("solid", fgColor="E8EEF5")
RED = PatternFill("solid", fgColor="F8D7DA"); AMB = PatternFill("solid", fgColor="FFF3CD"); OK = PatternFill("solid", fgColor="D4EDDA")
RP = '#,##0;(#,##0);-'
thin = Border(bottom=Side(style="thin", color="C0C0C0"))

# (id, folder, file, date, seller, order no, items, ship, ship voucher, platform voucher, protection, insurance, app fee, service fee, stated total)
PCB_PAID_RP = 579000   # what the JLCPCB order actually cost in Rp (from the user)
RATE = PCB_PAID_RP / 31.53   # effective Rp per USD, ~18,363
# USD invoices: id -> (merchandise, shipping, discount, grand total) in USD
USD = {"5-01": (16.51, 26.92, -11.90, 31.53)}
def rp(x): return round(x * RATE)
INV = [
 ("1-01","Invoice","2026-11-01 CNC STORE BANDUNG 586911437852935615.pdf","2026-11-01","CNC STORE BANDUNG","586911437852935615",237000,33000,-33000,-21564,7400,1700,712,720,225968),
 ("1-02","Invoice","2026-11-01 Putra Niaga Elektronik 586911452028175807.pdf","2026-11-01","Putra Niaga Elektronik","586911452028175807",42450,33000,-33000,-3860,0,500,137,117,39344),
 ("1-03","Invoice","2026-11-01 My Aladin 586911437852607935.pdf","2026-11-01","My Aladin","586911437852607935",50270,35000,-35000,-4576,4200,600,151,163,50808),
 ("1-04","Invoice","2026-11-01 BEST A&Y 586911527779534271.pdf","2026-11-01","BEST A&Y","586911527779534271",34485,29000,-29000,0,0,400,415,410,35710),
 ("1-05","Invoice","2026-11-01 I2C Parts 586911527779141055.pdf","2026-11-01","I2C Parts","586911527779141055",12250,22500,-22500,0,0,300,145,150,12845),
 ("1-06","Invoice","2026-11-01 Easy Go. 586911527779009983.pdf","2026-11-01","Easy Go.","586911527779009983",36800,21500,-21500,0,0,400,440,440,38080),
 ("1-07","Invoice","2026-11-01 EasyWare Electronics 586911713217775039.pdf","2026-11-01","EasyWare Electronics","586911713217775039",32000,18500,-18500,0,3000,400,1000,1000,37400),
 ("1-08","Invoice","2026-11-01 xyz garage 586911720159282623.pdf","2026-11-01","xyz garage","586911720159282623",140000,33000,-33000,0,0,1100,1000,1000,143100),
 ("1-09","Invoice","2026-11-01 Rajawali3D 586911951922955711.pdf","2026-11-01","Rajawali3D","586911951922955711",104000,34500,-34500,0,11200,900,521,549,117170),
 ("1-11","Invoice","2026-11-01 Lajarus Teknik 586911858803967423.pdf","2026-11-01","Lajarus Teknik","586911858803967423",94350,33000,-33000,0,2800,800,479,451,98880),
 ("1-12","Invoice","2026-11-01 Lajarus Teknik 586912141373179327.pdf","2026-11-01","Lajarus Teknik","586912141373179327",300000,99000,-94000,0,18000,2400,1000,1000,327400),
 ("1-13","Invoice","2026-11-01 Lajarus Teknik 586912365092898239.pdf","2026-11-01","Lajarus Teknik","586912365092898239",119000,33000,-33000,0,8400,1000,1000,1000,130400),
 ("1-14","Invoice","2026-11-01 Rajawali3D 586912453409670591.pdf","2026-11-01","Rajawali3D","586912453409670591",72000,34500,-34500,0,1400,700,1000,1000,76100),
 ("2-01","Invoice 2","2026-11-02 Rajawali3D 586916375205610943.pdf","2026-11-02","Rajawali3D","586916375205610943",199000,34500,-34500,0,0,1500,1000,1000,202500),
 ("2-03","Invoice 2","2026-11-02 CNC STORE BANDUNG 586916406310503871.pdf","2026-11-02","CNC STORE BANDUNG","586916406310503871",20600,18500,-18500,0,1400,300,1000,1000,24300),
 ("2-04","Invoice 2","2026-11-02 art techno new 586916427294410175.pdf","2026-11-02","art techno new","586916427294410175",13500,15000,-15000,0,0,200,1000,1000,15700),
 ("2-05","Invoice 2","2026-11-02 Sunly elektronik store 586916549279188415.pdf","2026-11-02","Sunly elektronik store","586916549279188415",109800,35000,-35000,0,0,900,1000,1000,112700),
 ("2-06","Invoice 2","2026-11-02 TNG.Industrial 586916724149814719.pdf","2026-11-02","TNG.Industrial","586916724149814719",11845,22500,-22500,0,0,300,1000,1000,14145),
 ("2-07","Invoice 2","2026-11-02 teknoza 586916646933857727.pdf","2026-11-02","teknoza","586916646933857727",113600,33000,-33000,0,0,900,1000,1000,116500),
 ("3-01","Invoice 3","2026-11-02 Lean Sigma 586921744697755071.pdf","2026-11-02","Lean Sigma","586921744697755071",84000,35000,-35000,-2520,0,800,1000,1000,84280),
 ("3-02","Invoice 3","2026-11-02 3Din Jakarta 586927666385225151.pdf","2026-11-02","3Din Jakarta","586927666385225151",180300,35000,-35000,0,0,1300,1000,1000,183600),
 ("3-03","Invoice 3","2026-11-02 Atoz Baut 586928034239841727.pdf","2026-11-02","Atoz Baut","586928034239841727",108250,70000,-65000,0,0,1100,1000,1000,116350),
 ("4-01","Downloads","2026-11-03 CNC STORE BANDUNG 586943662539113919.pdf","2026-11-03","CNC STORE BANDUNG","586943662539113919",188000,33000,-33000,-15000,0,1400,1000,1000,176400),
 ("4-02","Downloads","2026-11-03 3Din Jakarta 586945467695924671.pdf","2026-11-03","3Din Jakarta","586945467695924671",57850,35000,-32000,0,0,600,1000,1000,63450),
 ("4-03","Downloads","2026-11-03 Jogjarobotika 586945343438423487.pdf","2026-11-03","Jogjarobotika","586945343438423487",6000,20500,-20500,0,0,200,1000,0,7200),
 ("4-04","Downloads","2026-11-03 Nusantara Electrical Solusindo 586945313262503359.pdf","2026-11-03","Nusantara Electrical Solusindo","586945313262503359",12000,22500,-22500,0,1400,300,1000,1000,15700),
 ("4-05","Downloads","2026-11-03 Hendra Teknik 586945293656360383.pdf","2026-11-03","Hendra Teknik","586945293656360383",14500,15000,-15000,-435,0,200,1000,1000,16265),
 ("4-06","Downloads","2026-11-03 Daimaru 586945267565823423.pdf","2026-11-03","Daimaru","586945267565823423",10950,65600,-60000,0,0,500,1000,1000,19050),
 ("4-07","Downloads","2026-11-03 lapaktukang 586945991182157247.pdf","2026-11-03","lapaktukang","586945991182157247",23300,35000,-24000,0,0,400,1000,1000,36700),
 ("4-08","Downloads","2026-11-03 APNcikarang 586945867966285247.pdf","2026-11-03","APNcikarang","586945867966285247",32000,35000,-32000,0,0,500,1000,1000,37500),
 ("5-01","Downloads","2026-10-26 JLCPCB 8322107A2026102314246516.pdf","2026-10-26","JLCPCB","SMT026102361018-Y9",rp(16.51),rp(26.92),0,rp(-11.90),0,0,0,0,rp(31.53)),
 ("5-02","Downloads","2026-11-01 FedEx import tax AWB 879182532980.pdf","2026-11-01","FedEx (import duty + tax)","AWB 879182532980",176849,0,0,0,0,0,0,0,176849),
 ("5-03","Downloads","2026-11-04 Beaux Button Indonesia QRS1446982643.pdf","2026-11-04","Beaux Button Indonesia (3D print shop)","QRS1446982643",1416800,0,0,0,0,0,0,0,1416800),
 ("6-01","Manual","(no receipt; from the user)","","Anthropic (Claude Pro)","2 months",750000,0,0,0,0,0,0,0,750000),
]
# (invoice, item, qty, unit Rp, pcs per unit, key, use)
IT = [
 ("1-01","MG90S micro servo",2,34000,1,"mg90s","Finger A and B"),
 ("1-01","E-stop LA38-11ZS 22 mm",1,14500,1,"estop","Mast top"),
 ("1-01","XL4015 5 A buck",1,20600,1,"xl4015","16.8 V motor rail"),
 ("1-01","ESP32-S3 DevKitC-1 N16R8",1,133900,1,"esp32","Motion board MCU"),
 ("1-02","1N4007 diode",5,250,1,"pcb_parts","Motion board"),
 ("1-02","Male header 1x40",5,1000,1,"pcb_parts","Motion board"),
 ("1-02","Female header 1x40",5,2000,1,"pcb_parts","Motion board"),
 ("1-02","Active buzzer 5 V",2,2500,1,"pcb_parts","Motion board"),
 ("1-02","Terminal block 2-pin 5.08",5,1000,1,"pcb_parts","Motion board"),
 ("1-02","Elco 470 uF 35 V",4,1800,1,"pcb_parts","Motion board"),
 ("1-02","Elco 100 uF 35 V",8,500,1,"pcb_parts","Motion board"),
 ("1-02","Elco 220 uF 25 V",10,500,1,"pcb_parts","Motion board"),
 ("1-03","Dupont jumper 40-pin 10 cm, M-M",1,12600,1,"jumpers","Wiring"),
 ("1-03","Dupont jumper 40-pin 10 cm, M-F",1,12600,1,"jumpers","Wiring"),
 ("1-03","XT30 female with 16 AWG lead",1,15985,1,"xt30","Power to board"),
 ("1-03","XT30PW male, PCB",1,9085,1,"xt30","Power to board"),
 ("1-04","Microswitch KW11-3Z",15,2299,1,"kw11","Z/Y home, slot A/B + spares"),
 ("1-05","WS2812B 1-LED module",5,2450,1,"ws2812","Status LED"),
 ("1-06","JST-XH kit, 230 pcs",1,36800,1,"jst","Connectors"),
 ("1-07","XY-3606 5 V buck",1,32000,1,"xy3606","5 V logic"),
 ("1-08","TMC2209 (Makerbase MKS)",2,70000,1,"tmc2209","Z and Y drivers"),
 ("1-09","Mini V-wheel 105zz",8,13000,1,"vwheel","Z and Y carriages"),
 ("1-11","M5 nylock (SS)",15,650,1,"m5_nylock","Wheel axles, nut block, idler"),
 ("1-11","Flexible coupler 5x8",1,15000,1,"coupler","Z motor to lead screw"),
 ("1-11","Idler 2GT 20T no teeth, 5 mm bore",1,15000,1,"idler","Y belt"),
 ("1-11","2040 V-slot, per cm",42,1300,1,"v2040_cm","Mast 420 mm"),
 ("1-12","2020 V-slot, 1 m",4,75000,100,"v2020_cm","Rack, frame, Y rail, legs"),
 ("1-13","T8 anti-backlash nut block, lead 2",1,23000,1,"nutblock","Z carriage"),
 ("1-13","T8 lead screw lead 2, per 10 cm",4,19000,10,"leadscrew_cm","Cut to 350 mm"),
 ("1-13","GT2 belt 6 mm, per 100 cm",1,20000,100,"belt_cm","Y axis"),
 ("1-14","GT2 pulley 20T, 5 mm bore",1,12000,1,"pulley","Y motor"),
 ("1-14","Shim 8 x 5.1 x 1",10,2000,1,"shim","V-wheel stacks"),
 ("1-14","OpenBuilds eccentric spacer 6 mm",4,7000,1,"ecc","Z +x pair, Y lower pair"),
 ("1-14","OpenBuilds plain spacer 6 mm",4,3000,1,"spacer","Other 4 wheels"),
 ("2-01","M5 x 8 button head, pack of 10",6,10000,10,"m5x8","Corner brackets"),
 ("2-01","M5 x 12 button head, pack of 10",1,10000,10,"m5x12","Mast collar"),
 ("2-01","M5 T-nut drop-in",90,1100,1,"tnut","Frame, brackets, shelves"),
 ("2-01","M5 x 10 button head, pack of 10",3,10000,10,"m5x10","Deck, shelves, top plate"),
 ("2-03","XL4015 5 A buck",1,20600,1,"xl4015","5.8 V servo rail"),
 ("2-04","Dupont jumper F-F 30 cm, 40-pin",1,13500,1,"jumpers","Servo extensions"),
 ("2-05","Adaptor 24 V 5 A",1,109800,1,"adapter","Replaces Delta PSU"),
 ("2-06","KFL08 flange bearing",1,11845,1,"kfl08","Lead screw top"),
 ("2-07","Silicone wire 18 AWG black",1,13000,1,"wire","Power"),
 ("2-07","Silicone wire 18 AWG red",1,13000,1,"wire","Power"),
 ("2-07","Silicone wire 22 AWG black",3,7100,1,"wire","Motors / supply"),
 ("2-07","Silicone wire 22 AWG red",3,7100,1,"wire","Motors / supply"),
 ("2-07","Silicone wire 26 AWG black",3,5000,1,"wire","Signals"),
 ("2-07","Silicone wire 26 AWG red",3,5000,1,"wire","Signals"),
 ("2-07","Silicone wire 26 AWG yellow",3,5000,1,"wire","Signals"),
 ("3-01","2020 corner bracket (gusset)",28,3000,1,"bracket","Rack + robot frame"),
 ("3-02","M5 x 10 countersunk (DIN7991, SS)",10,1100,1,"m5x10cs","Y idler bracket"),
 ("3-02","M5 nylock (SS)",20,500,1,"m5_nylock","Spare"),
 ("3-02","M5 hex nut (SS)",20,350,1,"m5_nut","Base board through-bolts"),
 ("3-02","M3 x 4 knurled insert",33,1000,1,"ins_m3","Robot 8 + dummy lids 16"),
 ("3-02","M4 nylock (SS)",10,450,1,"m4_nut","KFL08"),
 ("3-02","M5 T-nut drop-in",20,800,1,"tnut","Extra"),
 ("3-02","M5 x 8 knurled insert",15,3200,1,"ins_m5","Tray back plate"),
 ("3-02","Self-tapping 3.5 x 9.5, flat end (SS)",20,600,1,"st35","Dummy drive? see Notes"),
 ("3-02","Self-tapping 3.5 x 6.5, flat end (SS)",40,600,1,"st35","Dummy drive? see Notes"),
 ("3-02","M4 x 16 socket head (SS)",20,740,1,"m4x16","KFL08"),
 ("3-03","M5 x 8 socket head (SS)",60,670,1,"m5x8","Corner brackets"),
 ("3-03","M5 x 16 socket head (SS)",15,810,1,"m5x16","Collar, tray bolts, rail bracket"),
 ("3-03","M5 x 10 flat head Phillips (SS)",10,350,1,"m5x10cs","Spare countersunk"),
 ("3-03","M5 x 20 socket head (SS)",10,900,1,"m5x20","Nut block"),
 ("3-03","M5 x 30 socket head (SS)",10,1190,1,"m5x30","V-wheel axles"),
 ("3-03","M5 x 10 socket head (SS)",20,680,1,"m5x10","Deck, shelves"),
 ("3-03","M5 x 12 socket head (SS)",10,720,1,"m5x12","Mast collar"),
 ("3-03","M5 x 25 socket head (SS)",10,1070,1,"m5x25","Tray through bracket, idler axle"),
 ("4-01","NEMA17 17HS4401 1.5 A 40 N.cm + 6-to-4 pin Dupont cable",2,94000,1,"nema17","Z and Y"),
 ("4-02","M3 x 6 button head (ISO 7380, SS)",22,400,1,"m3x6","E-stop, PCB, dummy lids"),
 ("4-02","M3 x 8 button head (ISO 7380, SS)",15,500,1,"m3x8","Z and Y motors"),
 ("4-02","M3 x 10 button head (ISO 7380, SS)",15,550,1,"m3x10","Belt clamp"),
 ("4-02","M3 x 12 button head (ISO 7380, SS)",15,600,1,"m3x12","Z mount, electronics tray"),
 ("4-02","M5 x 40 socket head (DIN 912, SS)",15,1300,1,"m5x40","Base board"),
 ("4-02","M5 washer 10 x 0.8 (SS)",20,240,1,"m5_washer","Base board"),
 ("4-03","JST-XH 4-pin cable, plugs both ends, 20 cm",2,3000,1,"jst_xh4","Cut in half: 4 stepper pigtails"),
 ("4-04","22 mm push-button box, 1 hole (white)",1,12000,1,"estop_box","E-stop housing"),
 ("4-05","HSS drill bit 7.0 mm",1,7250,1,"drill7","Eccentric holes"),
 ("4-05","HSS drill bit 7.5 mm",1,7250,1,"drill75","Eccentric holes"),
 ("4-06","Double foam tape 24 mm x 5 m",1,10950,1,"tape","Wiring"),
 ("4-07","M3 hex nut (SS 304)",10,330,1,"m3_nut","Z mount, electronics tray"),
 ("4-07","M3 x 8 Phillips pan head (SS), pack of 50",1,20000,50,"st_m3","Dummy drives: machine thread, forms its own thread in the ~2.5 mm pilot"),
 ("4-08","M2 x 10 pan head, pack of 50",1,10000,50,"m2x10","Microswitches (machine thread)"),
 ("4-08","M2 x 6 self-tapping pan head, pack of 50",1,15000,50,"m2x6","Finger to horn"),
 ("4-08","M2 x 8 pan head, pack of 50",1,7000,50,"m2x8","Servo tabs (machine thread)"),
 ("5-01","Motion board PCBA, 5 boards (rbg3-motion, USD 16.51)",1,rp(16.51),5,"pcb","Motion board; 4 spares"),
 ("5-02","Import duty + taxes on the JLCPCB boards (FedEx, bank transfer)",1,176849,1,"import_tax","PCB import"),
 ("5-03","3D printing, rig parts (PETG, QRIS payment)",1,1416800,1,"print","Rig printed parts: 3 caddies, 2 bay shelves, no dummies"),
 ("6-01","Claude Pro subscription, 2 months",1,750000,1,"claude","Design, CAD, firmware, docs"),
]
# (key, item, need, unit, note) - rig needs from the CAD fastener model + rig page
NEED = [
 ("Motion and control",),
 ("pcb","Motion board PCB (assembled)",1,"pcs","JLCPCB, 5 boards"),
 ("esp32","ESP32-S3 DevKitC-1",1,"pcs",""),
 ("tmc2209","TMC2209 driver",2,"pcs","Firmware patch needed for a 2-driver board"),
 ("xl4015","XL4015 buck",2,"pcs","16.8 V and 5.8 V"),
 ("xy3606","XY-3606 5 V buck",1,"pcs",""),
 ("estop","E-stop LA38-11ZS",1,"pcs",""),
 ("adapter","Adaptor 24 V 5 A",1,"pcs","Do not feed 24 V straight to the board (18 V TVS)"),
 ("mg90s","MG90S servo",2,"pcs","A spare is recommended"),
 ("kw11","KW11-3Z microswitch",4,"pcs","Z home, Y home, slot A, slot B"),
 ("ws2812","WS2812B LED",5,"pcs",""),
 ("nema17","NEMA17 (17HS4401 bought)",2,"pcs","Z and Y. Re-terminate the Dupont plug to JST-XH 4-pin (2B, 2A, 1A, 1B)"),
 ("Frame and motion",),
 ("v2020_cm","2020 V-slot",346,"cm","Rack 208 + frame 93 + Y rail 28.5 + legs 16.8"),
 ("v2040_cm","2040 V-slot",42,"cm","Mast"),
 ("bracket","2020 corner bracket",26,"pcs","Estimate from the rig page; count the joints"),
 ("vwheel","Mini V-wheel",8,"pcs",""),
 ("ecc","Eccentric spacer",4,"pcs",""),
 ("spacer","Plain spacer",4,"pcs",""),
 ("shim","Shim 8 x 5 x 1",8,"pcs","1 per wheel"),
 ("leadscrew_cm","T8 lead screw",35,"cm",""),
 ("nutblock","Anti-backlash nut block",1,"pcs",""),
 ("coupler","Coupler 5x8",1,"pcs",""),
 ("kfl08","KFL08 bearing",1,"pcs",""),
 ("belt_cm","GT2 belt",70,"cm","Approx. loop"),
 ("pulley","GT2 pulley 20T",1,"pcs",""),
 ("idler","Idler 20T",1,"pcs",""),
 ("Fasteners",),
 ("m5x8","M5 x 8",52,"pcs","2 per corner bracket"),
 ("m5x10","M5 x 10",25,"pcs","Robot 7 + shelves 18. Use BUTTON heads on the shelves"),
 ("m5x10cs","M5 x 10 countersunk",1,"pcs","Y idler bracket"),
 ("m5x12","M5 x 12",6,"pcs","Mast collar"),
 ("m5x16","M5 x 16",11,"pcs",""),
 ("m5x20","M5 x 20",2,"pcs","Nut block"),
 ("m5x25","M5 x 25",4,"pcs",""),
 ("m5x30","M5 x 30",8,"pcs","V-wheel axles"),
 ("m5x40","M5 x 40 (base board)",12,"pcs","Legs and rack feet to 18 mm plywood (or wood screws)"),
 ("tnut","M5 T-nut",96,"pcs","Robot 18 + brackets 52 + shelves 18 + board 8"),
 ("m5_nylock","M5 nylock",11,"pcs",""),
 ("m5_nut","M5 hex nut",12,"pcs","Only if the board is through-bolted"),
 ("m5_washer","M5 washer",20,"pcs","Base board bolts + spares"),
 ("m4x16","M4 x 16",2,"pcs","KFL08"),
 ("m4_nut","M4 nut",2,"pcs","KFL08"),
 ("m3x6","M3 x 6",22,"pcs","E-stop 2, PCB 4, dummy lids 16"),
 ("m3x8","M3 x 8",8,"pcs","Z and Y motors"),
 ("m3x10","M3 x 10",2,"pcs","Belt clamp"),
 ("m3x12","M3 x 12",4,"pcs","Z mount + electronics tray to deck"),
 ("m3_nut","M3 hex nut",4,"pcs",""),
 ("st_m3","Self-tapping for dummy drives",24,"pcs","Pilot prints ~2.5 mm: M3 self-tap. The 3.5 mm screws bought need a bigger pilot, see Notes"),
 ("st35","Self-tapping 3.5 (bought)",0,"pcs","Not in the design; see Notes"),
 ("m2x6","M2 x 6 self-tapping",4,"pcs","Finger to horn"),
 ("m2x8","M2 x 8 self-tapping",4,"pcs","Servo tabs (MG90S screws may do)"),
 ("m2x10","M2 x 10 self-tapping",8,"pcs","Microswitches"),
 ("ins_m3","M3 x 4 insert",24,"pcs",""),
 ("ins_m5","M5 x 8 insert",10,"pcs",""),
]
TODO = [
 ("Heat-shrink 2 / 3 / 6 mm + cable ties",1,25000,"Wiring (local shop)"),
 ("Laser-cut deck (quoted, not paid yet)",1,75000,"Polaris Laser Bali, cad/DXF/robot/deck.dxf"),
 ("Steel ballast ~0.9 kg (flat bar / washers) + epoxy",1,50000,"Bolted into the 2 moving caddies, ~450 g each (no dummy drives)"),
 ("Print shipping, Paxel L, Bekasi to Kuta (estimate from the user)",1,157000,"3D-printed parts, 35 x 30 x 25 cm box"),
 ("Inline fuse holder 5x20 (min. order 3)",3,3000,"3 A fuse after the 16.8 V buck (review 6 Nov). Tokopedia cart: King Wijaya, Denpasar"),
 ("Glass fuse 5x20 mm 3 A (min. order 10)",10,1940,"For the fuse holder; spares. King Wijaya"),
 ("DC jack pigtail, female (min. order 3)",3,2910,"24 V adapter plug to the XL4015 input. King Wijaya"),
 ("Drill bit 2 mm (min. order 3)",3,3880,"Servo horn holes. King Wijaya"),
 ("HSS drill 7.2 mm (YG1)",1,46391,"Opens the 7.7 eccentric holes (print ~7.05) to 7.2. Podomoro Teknik, Bekasi"),
 ("Servo extension F-M 50 cm",2,7566,"Fingers ride Y on Z; the F-F jumpers can't extend servo plugs. My Aladin, Bekasi"),
 ("Spiral wrap 10 mm x 8 m",1,21381,"Moving harness over Z and Y. Life Habits, Denpasar"),
 ("Perfboard backup kit for the motion board",1,50000,"Only built if the PCB fails bring-up. Tokopedia King Wijaya (Denpasar), "
  "~Rp45,100: perfboard 9x15, 100 uF/35 V x2, 470 uF/35 V x2, female header 1x40 x3. Local shop: resistors 1k x6, 10k x10, "
  "100k, 330R x2 (18k replaced by a 110k/20k divider, VMOT_DIVIDER = 6.5) and a male header"),
]

wb = Workbook()
def sheet(ws, headers, widths):
    for i, (h, w) in enumerate(zip(headers, widths), 1):
        c = ws.cell(1, i, h); c.font = HEAD; c.fill = HFILL; c.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[L(i)].width = w
    ws.freeze_panes = "A2"; ws.row_dimensions[1].height = 30

# Summary
S = wb.active; S.title = "Summary"
# Invoices
I = wb.create_sheet("Invoices")
ih = ["ID","Batch","File","Date","Seller","Order no.","Items (Rp)","Shipping","Shipping voucher","Platform voucher",
      "Protection","Insurance","App fee","Service fee","Total (Rp)","Invoice total","Check"]
sheet(I, ih, [7,10,22,11,22,21,12,10,11,11,10,10,9,9,12,12,8])
for r, v in enumerate(INV, 2):
    for c, x in enumerate(v[:14], 1):
        cell = I.cell(r, c, x); cell.font = BLUE if c >= 7 else BLK
        if c >= 7: cell.number_format = RP
    if v[0] in USD:
        mu, sh, dc, gt = USD[v[0]]; rc = f"$C${len(INV) + 5}"
        for c, x in ((7, mu), (8, sh), (10, dc)): I.cell(r, c, f"=ROUND({x}*{rc},0)")
    I.cell(r, 15, f"=SUM(G{r}:N{r})").number_format = RP
    I.cell(r, 16, v[14] if v[0] not in USD else f"=ROUND({USD[v[0]][3]}*$C${len(INV) + 5},0)").font = BLUE; I.cell(r, 16).number_format = RP
    I.cell(r, 17, f'=IF(ABS(O{r}-P{r})<=2,"OK","CHECK")')
    for c in range(1, 18): I.cell(r, c).border = thin
    for c in (15, 17): I.cell(r, c).font = BLK
n = len(INV) + 1; t = n + 1
I.cell(t, 5, "Total").font = BOLD
for c in range(7, 17):
    I.cell(t, c, f"=SUM({L(c)}2:{L(c)}{n})").number_format = RP; I.cell(t, c).font = BOLD; I.cell(t, c).fill = TFILL
I.cell(t + 2, 1, "Source: receipts in docs/budget/invoices (File column; blue = typed from the receipt). Batch = the folder they first came in. "
       "Identical copies (AirDrop resends, 'marketplace' files) were left out (counted once).").font = Font(name=F, italic=True)
I.cell(t + 3, 1, "Effective rate (Rp per USD) for the JLCPCB invoice: Rp579,000 actually paid / USD 31.53 (from the user)").font = BOLD
I.cell(t + 3, 3, f"={PCB_PAID_RP}/31.53").font = BLUE; I.cell(t + 3, 3).fill = PatternFill("solid", fgColor="FFFF00"); I.cell(t + 3, 3).number_format = "#,##0.00"
I.cell(t + 4, 1, "JLCPCB invoice 8322107A2026102314246516, 26 Oct 2026: 5 assembled motion boards USD 16.51 + FedEx USD 26.92 - discount USD 11.90 = USD 31.53.").font = Font(name=F, italic=True)

# Items
T = wb.create_sheet("Items")
th = ["Invoice","Seller","Item","Qty","Unit (Rp)","Line (Rp)","Pcs per qty","Pieces","Key","Used for"]
sheet(T, th, [8,22,40,6,11,12,9,8,13,32])
seller = {v[0]: v[4] for v in INV}
for r, v in enumerate(IT, 2):
    inv, item, q, u, ppu, key, use = v
    T.cell(r, 1, inv); T.cell(r, 2, f'=INDEX(Invoices!$E$2:$E${n},MATCH(A{r},Invoices!$A$2:$A${n},0))').font = GREEN
    T.cell(r, 3, item); T.cell(r, 4, q).font = BLUE; T.cell(r, 5, u).font = BLUE; T.cell(r, 5).number_format = RP
    if inv in USD: T.cell(r, 5, f"=ROUND({USD[inv][0]}*Invoices!$C${len(INV) + 5},0)").font = GREEN
    T.cell(r, 6, f"=D{r}*E{r}").number_format = RP
    T.cell(r, 7, ppu).font = BLUE; T.cell(r, 8, f"=D{r}*G{r}"); T.cell(r, 9, key); T.cell(r, 10, use)
    for c in range(1, 11): T.cell(r, c).border = thin
    for c in (1, 3, 9, 10): T.cell(r, c).font = BLK
m = len(IT) + 1
T.cell(m + 1, 3, "Total items").font = BOLD
T.cell(m + 1, 6, f"=SUM(F2:F{m})").number_format = RP; T.cell(m + 1, 6).font = BOLD; T.cell(m + 1, 6).fill = TFILL
T.cell(m + 2, 3, "Check vs Invoices 'Items (Rp)'").font = Font(name=F, italic=True)
T.cell(m + 2, 6, f'=IF(F{m+1}=Invoices!G{t},"OK","CHECK")')

# Rig check
R = wb.create_sheet("Rig check")
sheet(R, ["Item","Need","Bought","Short","Unit","Status","Note"], [34,8,8,8,6,10,60])
r = 2
for v in NEED:
    if len(v) == 1:
        c = R.cell(r, 1, v[0]); c.font = BOLD; c.fill = TFILL
        for k in range(2, 8): R.cell(r, k).fill = TFILL
        r += 1; continue
    key, item, need, unit, note = v
    R.cell(r, 1, item); R.cell(r, 2, need).font = BLUE
    R.cell(r, 3, f'=SUMIFS(Items!$H$2:$H${m},Items!$I$2:$I${m},"{key}")').font = GREEN
    R.cell(r, 4, f"=MAX(0,B{r}-C{r})")
    R.cell(r, 5, unit)
    R.cell(r, 6, f'=IF(B{r}=0,"CHECK",IF(D{r}>0,IF(C{r}=0,"MISSING","SHORT"),"OK"))')
    R.cell(r, 7, note); R.cell(r, 7).alignment = Alignment(wrap_text=True)
    R.cell(r, 9, key).font = Font(name=F, color="999999")
    for k in range(1, 8): R.cell(r, k).border = thin
    r += 1
R.column_dimensions["I"].width = 12; R.cell(1, 9, "key").font = Font(name=F, color="999999")
from openpyxl.formatting.rule import CellIsRule
R.conditional_formatting.add(f"F2:F{r}", CellIsRule(operator="equal", formula=['"MISSING"'], fill=RED))
R.conditional_formatting.add(f"F2:F{r}", CellIsRule(operator="equal", formula=['"SHORT"'], fill=AMB))
R.conditional_formatting.add(f"F2:F{r}", CellIsRule(operator="equal", formula=['"CHECK"'], fill=AMB))
R.conditional_formatting.add(f"F2:F{r}", CellIsRule(operator="equal", formula=['"OK"'], fill=OK))
R.cell(r + 1, 1, "Need: CAD fastener model (cad/src/lib/robot_fasteners.py, rig joints only) + rig page; blue = input. "
       "Electronics for the motion PCB (elcos, headers, diodes, terminals, buzzer) are not checked against the PCB BOM here.").font = Font(name=F, italic=True)
rc_last = r - 1

# Still to buy
B = wb.create_sheet("Still to buy")
sheet(B, ["Item","Qty","Unit est. (Rp)","Line est. (Rp)","Note"], [48,6,13,13,50])
for i, (item, q, u, note) in enumerate(TODO, 2):
    B.cell(i, 1, item); B.cell(i, 2, q).font = BLUE; B.cell(i, 3, u).font = BLUE; B.cell(i, 3).number_format = RP
    B.cell(i, 4, f"=B{i}*C{i}").number_format = RP; B.cell(i, 5, note)
    for c in range(1, 6): B.cell(i, c).border = thin
k = len(TODO) + 1
B.cell(k + 1, 1, "Total still to buy (estimate)").font = BOLD
B.cell(k + 1, 4, f"=SUM(D2:D{k})").number_format = RP; B.cell(k + 1, 4).font = BOLD; B.cell(k + 1, 4).fill = TFILL
B.cell(k + 2, 1, "3D printing: paid 4 Nov (Invoices 5-03), nothing left to pay")
B.cell(k + 2, 4, 0).font = BLUE; B.cell(k + 2, 4).number_format = RP
B.cell(k + 2, 5, "Paid Rp1,416,800 vs the Rp1,380,500 estimate (=(1383-133-88+93)*1100). Shop quote 4 Nov: PETG 1,383 g at Rp1,100/g + PLA 524 g at Rp999/g (Rp2,044,776). Cut to 3 caddies (-133 g), "
       "2 bay shelves (-88 g), no PLA dummy drives; + z_carriage ~93 g (estimate, missing from the quote). Coupon paid separately")
B.cell(k + 4, 1, "Estimates from the rig page and docs/rig-order.md; check prices before paying.").font = Font(name=F, italic=True)

# Summary content
S.column_dimensions["A"].width = 44; S.column_dimensions["B"].width = 16
S["A1"] = "Corvin rig: purchases so far"; S["A1"].font = Font(name=F, bold=True, size=14)
rows = [
 ("Invoices (unique)", f"=COUNTA(Invoices!A2:A{n})", "0"),
 ("Items subtotal (Rp)", f"=Invoices!G{t}", RP),
 ("Shipping after vouchers (Rp)", f"=Invoices!H{t}+Invoices!I{t}", RP),
 ("Platform vouchers (Rp)", f"=Invoices!J{t}", RP),
 ("Protection, insurance, fees (Rp)", f"=SUM(Invoices!K{t}:N{t})", RP),
 ("Total paid (Rp)", f"=Invoices!O{t}", RP),
 ("  of which folder Invoice + Invoice 2 (Rp)", f'=SUMIFS(Invoices!O2:O{n},Invoices!B2:B{n},"Invoice")+SUMIFS(Invoices!O2:O{n},Invoices!B2:B{n},"Invoice 2")', RP),
 ("  of which folder Invoice 3 (Rp)", f'=SUMIFS(Invoices!O2:O{n},Invoices!B2:B{n},"Invoice 3")', RP),
 ("  of which loose in Downloads (3-4 Nov, JLCPCB, FedEx, print) (Rp)", f'=SUMIFS(Invoices!O2:O{n},Invoices!B2:B{n},"Downloads")', RP),
 ("  of which entered by hand, no receipt (Rp)", f'=SUMIFS(Invoices!O2:O{n},Invoices!B2:B{n},"Manual")', RP),
 ("", None, None),
 ("Still to buy, estimate (Rp)", f"='Still to buy'!D{k+1}", RP),
 ("3D printing still to pay (paid: Invoices 5-03) (Rp)", f"='Still to buy'!D{k+2}", RP),
 ("Rig total, estimate (Rp)", "=B8+B14+B15", RP),
 ("", None, None),
 ("Rig check: items missing", f"=COUNTIF('Rig check'!F2:F{rc_last},\"MISSING\")", "0"),
 ("Rig check: items short", f"=COUNTIF('Rig check'!F2:F{rc_last},\"SHORT\")", "0"),
 ("All invoice totals match receipts", f'=IF(COUNTIF(Invoices!Q2:Q{n},"OK")=B3,"YES","NO")', None),
]
for i, (a, f, fmt) in enumerate(rows, 3):
    S.cell(i, 1, a).font = BLK
    if f is not None:
        c = S.cell(i, 2, f); c.font = GREEN if "!" in f else BLK
        if fmt: c.number_format = fmt
for i in (8, 16): S.cell(i, 1).font = BOLD; S.cell(i, 2).font = Font(name=F, bold=True, color="008000" if i == 8 else "000000")

N = wb.create_sheet("Notes")
N.column_dimensions["A"].width = 120
notes = [
 "Notes",
 "1. Duplicates: Invoice/PDF document 10 = 9 (Rajawali3D V-wheels) and 15 = 8 (xyz garage TMC2209). Counted once. Every 'marketplace' file is a copy of a PDF.",
 "2. The rig page said Saleh paid Rp1,857,950 for 20 orders; the receipts for folders Invoice + Invoice 2 add up to Rp1,857,450 (Rp500 less),",
 "   before the Bosch relay order was cancelled (note 14).",
 "3. Self-tapping 3.5 mm screws (3Din, 20 x 9.5 + 40 x 6.5): the dummy-drive holes are pilots for M3 self-tappers (design 2.85, prints ~2.5).",
 "   A 3.5 mm screw in a ~2.5 mm hole in a 1.9 mm wall is likely to split the PLA. Either buy M3 self-tappers, or raise M3_SELF_TAP_D",
 "   (cad/src/lib/dims.py) to ~3.3 before printing so it prints ~2.9-3.0 for the 3.5 mm screws.",
 "4. Atoz Baut M5 screws are SOCKET heads (taller, Ø8.5 x 5). Use the Rajawali3D BUTTON heads where the design has counterbores, mainly the",
 "   bay shelves (M5 x 10 into the frame): a socket head stands ~2 mm proud in the caddy channel. Socket heads are fine on corner brackets.",
 "5. Plenty of spares bought on M5 x 8/10/12/20/25 and M4 x 16 (20 for 2 needed).",
 "6. NEMA17 bought 3 Nov: 2 x 17HS4401 (CNC Store Bandung, Rp94,000 each, Rp176,400 paid). Its cable ends in a Dupont plug; the board has",
 "   JST-XH 4-pin (J6 Z, J7 Y): re-crimp to XH in the order 2B, 2A, 1A, 1B (find the coil pairs with a meter, ~1.5 ohm each).",
 "7. 3 Nov second batch (5 orders, Rp121,665): M3 x6/8/10/12 BUTTON heads (fit the M3 counterbores), M5 x 40 + washers,",
 "   JST-XH cables, button box, 7.0 / 7.5 mm bits, foam tape. AirDrop resends: 'marketplace 3'-'9' and two PDFs are copies, counted once.",
 "8. Atoz Baut M5 x 10 flat head says 'Drat P0.5' (fine thread): test one in a T-nut; use the 3Din DIN 7991 countersunk on the idler bracket.",
 "9. 3 Nov third batch (lapaktukang Rp36,700, APNcikarang Rp37,500): M3 nuts, M3 x 8 PH x50, M2 x6 self-tapping, M2 x8 / x10.",
 "   The M3 x 8 PH and M2 x8 / x10 are MACHINE screws, not self-tappers. In printed pilots sized to the tap drill (M3 ~2.5, M2 ~1.6)",
 "   they form their own thread: drive slowly, back out once to clear, do not over-tighten. Fine for the dummy drives and switches.",
 "10. Motion PCB: JLCPCB invoice (26 Oct), 5 assembled boards, USD 31.53 incl. FedEx; Rp579,000 actually paid (~Rp18,363/USD).",
 "    The rate cell on Invoices is =579000/31.53: change the 579000 if the statement shows a different amount.",
 "11. FedEx import duty + taxes on the PCBs (AWB 879182532980, paid 1 Nov 2026 by bank transfer): Rp176,849, no withholding tax.",
 "    Landed cost of the motion boards = JLCPCB total + this bill.",
 "12. Claude Pro, 2 months, Rp750,000: entered by hand from the user (folder 'Manual'), no receipt in Downloads.",
 "13. 3D printing (4 Nov, QRIS to Beaux Button Indonesia, Bekasi): Rp1,416,800 for the rig parts, cut to 3 caddies and 2 bay shelves,",
 "    no PLA dummy drives. The hole coupon was paid separately before. Shipping to Bali is on Still to buy.",
 "14. Bosch 12 V relay (Putra jaya autopart, order 586916367026062783, Rp38,400, 2 Nov) was cancelled and is left out. The E-stop NC",
 "    contact is wired straight in series with VMOT (under 2 A at 12-16.8 V, wire >= 0.5 mm2). The receipt stays in the invoices folder.",
]
for i, s in enumerate(notes, 1):
    N.cell(i, 1, s).font = BOLD if i == 1 else BLK
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if c.font.name != F: c.font = Font(name=F, bold=c.font.bold, italic=c.font.italic, color=c.font.color)
wb.save(OUT)
# Python cross-check of the numbers the formulas will produce
tot = sum(sum(v[6:14]) for v in INV); stated = sum(v[14] for v in INV)
print("total", tot, "stated", stated, "mismatch", [v[0] for v in INV if sum(v[6:14]) != v[14]])
items = {}
for v in IT: items[v[0]] = items.get(v[0], 0) + v[2] * v[3]
print("items vs subtotal mismatch", [(v[0], items.get(v[0]), v[6]) for v in INV if items.get(v[0]) != v[6]])
print("folder1+2", sum(v[14] for v in INV if v[1] != "Invoice 3"), "folder3", sum(v[14] for v in INV if v[1] == "Invoice 3"))
print("todo", sum(q * u for _, q, u, _ in TODO))
bought = {}
for v in IT: bought[v[5]] = bought.get(v[5], 0) + v[2] * v[4]
for v in NEED:
    if len(v) > 1 and bought.get(v[0], 0) < v[2]: print("short", v[0], v[2], bought.get(v[0], 0))
