// Scene overlays of the technical film. Every number on screen comes from spec v0.1.31 (docs/spec); targets are
// labelled as targets and the mission clock as simulated time.
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {AXLE_Y, H_BAY, TAG_APPROACH} from '../constants';
import {robotToWorld, spareToWorld, V3} from '../geom';
import {PowerTree} from './diagrams';
import {BLUE} from './theme';
import {EXPLODE, explodeAt, MISSION_END, SceneId, stateAt, STEPS, stepStart, toasts, TS} from './timeline';
import {at, Callout, GROTESK, Headline, INTER, inOut, Kicker, lerpNum, MONO, Panel, ramp, Readout, Shade, Specs, Why, window01} from './ui';

const ease = (t: number) => 1 - Math.pow(1 - t, 3);

/** World point of a robot model point (CAD mm), following the robot pose and the exploded offset of `part`. */
function rp(m: V3, f: number, part?: string): V3 {
  const s = stateAt(f);
  const e = explodeAt(f);
  const o = part ? EXPLODE[part] ?? [0, 0, 0] : [0, 0, 0];
  return robotToWorld([m[0] + o[0] * e, m[1] + o[1] * e, m[2] + o[2] * e], s);
}

const Scene: React.FC<{id: SceneId; children: (f: number, a: number, b: number) => React.ReactNode}> = ({id, children}) => {
  const f = useCurrentFrame();
  const [a, b] = TS[id];
  if (f < a || f >= b) return null;
  return <AbsoluteFill>{children(f, a, b)}</AbsoluteFill>;
};

/** Left text column: number + kicker, headline, then the scene's body. */
const Column: React.FC<{f: number; a: number; b: number; n: string; kicker: string; title: string; children?: React.ReactNode; top?: number}> = ({f, a, b, n, kicker, title, children, top = 110}) => (
  <>
    <Shade k={window01(f, a, b, 12)} />
    <div style={{position: 'absolute', left: 110, top, width: 720, ...inOut(f, a, b)}}>
      <Kicker n={n} text={kicker} at={a + 4} />
      <div style={{height: 22}} />
      <Headline text={title} at={a + 10} />
      <div style={{height: 34}} />
      {children}
    </div>
  </>
);

// ---------------------------------------------------------------- intro
export const Intro: React.FC = () => (
  <Scene id="intro">
    {(f, a, b) => {
      const out = ramp(f, b - 16, 16);
      const letters = 'CORVIN'.split('');
      const sheen = interpolate(f, [50, 100], [-30, 130], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
      return (
        <>
          <Shade k={0.85 * (1 - out)} width={55} />
          <div style={{position: 'absolute', left: 130, top: 300, opacity: 1 - out, transform: `translateY(${-out * 14}px)`}}>
            <Kicker text="Delta Cup 2026 · Automation track" at={a + 8} />
            <div style={{height: 26}} />
            <div style={{position: 'relative', display: 'flex', fontFamily: GROTESK, fontWeight: 700, fontSize: 190, letterSpacing: 6, lineHeight: 1, color: BLUE.ink}}>
              {letters.map((c, i) => {
                const k = ease(ramp(f, a + 16 + i * 3, 18));
                return (
                  <span key={i} style={{display: 'inline-block', overflow: 'hidden', paddingBottom: 14}}>
                    <span style={{display: 'inline-block', transform: `translateY(${(1 - k) * 105}%)`, opacity: k}}>{c}</span>
                  </span>
                );
              })}
              <div style={{position: 'absolute', inset: 0, background: `linear-gradient(100deg, transparent ${sheen - 12}%, rgba(56,211,255,0.55) ${sheen}%, transparent ${sheen + 12}%)`, mixBlendMode: 'screen', pointerEvents: 'none'}} />
            </div>
            <div style={{width: 520 * ease(ramp(f, a + 40, 24)), height: 3, background: `linear-gradient(90deg, ${BLUE.cyan}, rgba(56,211,255,0))`, marginTop: 8}} />
            <div style={{height: 28}} />
            <Headline text="Making drive replacement *easier.*" at={a + 52} size={54} />
            <div style={{height: 46}} />
            <div style={{fontFamily: MONO, fontSize: 21, letterSpacing: 4, color: BLUE.dim, opacity: ramp(f, a + 80, 16)}}>BOYS GO TO THAILAND · BRAWIJAYA UNIVERSITY</div>
          </div>
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 01 system
const Link: React.FC<{p: {x: number; y: number}; q: {x: number; y: number}; k: number; f: number; label: string}> = ({p, q, k, f, label}) => {
  const mx = (p.x + q.x) / 2;
  const my = Math.min(p.y, q.y) - 140;
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, opacity: k}}>
      <path d={`M${p.x},${p.y} Q${mx},${my} ${q.x},${q.y}`} fill="none" stroke={BLUE.blue} strokeWidth={2.5} strokeDasharray="8 10" strokeDashoffset={-f * 1.6} />
      <rect x={mx - 118} y={(p.y + q.y) / 2 - 92} width={236} height={36} rx={18} fill="rgba(8,26,42,0.85)" stroke={BLUE.blue} strokeOpacity={0.6} />
      <text x={mx} y={(p.y + q.y) / 2 - 68} textAnchor="middle" fontFamily={MONO} fontSize={16} fill={BLUE.blue}>{label}</text>
    </svg>
  );
};

export const System: React.FC = () => (
  <Scene id="system">
    {(f, a, b) => {
      const rack = at([0, 60, 380], f);
      const base = at(spareToWorld([0, 60, 290]), f);
      const robot = at(rp([0, -230, 560], f), f);
      const until = b - 6;
      return (
        <>
          <div style={{position: 'absolute', left: 110, top: 90, width: 1000, ...inOut(f, a, b)}}>
            <Kicker n="01" text="The system" at={a + 4} />
            <div style={{height: 20}} />
            <Headline text="One robot, one rack, *one base station.*" at={a + 10} size={60} />
          </div>
          <Callout x={rack.x} y={rack.y} lx={rack.x - 60} ly={rack.y - 120} at={a + 40} until={until} title="Rack · 4 bays" sub="ESP32 controller · Delta 24 V PSU" align="right" />
          <Callout x={base.x} y={base.y} lx={base.x - 200} ly={base.y + 60} at={a + 56} until={until} title="Base station (home)" sub="charging dock · spare + RMA slots" align="right" />
          <Callout x={robot.x} y={robot.y} lx={robot.x - 160} ly={robot.y - 200} at={a + 72} until={until} title="Corvin" sub="Pi 3 + ESP32-S3 motion board" align="right" />
          <Link p={robot} q={rack} k={window01(f, a + 110, until, 14)} f={f} label="Wi-Fi · Modbus TCP" />
          <div style={{position: 'absolute', left: 110, bottom: 90, display: 'flex', gap: 18, ...inOut(f, a + 150, b)}}>
            {[['1 job', 'base → rack → base'], ['2 drives', 'spare in · failed out'], ['0 walks', 'no technician trip']].map(([big, sub], i) => (
              <Panel key={i} style={{padding: '16px 24px', opacity: ease(ramp(f, a + 150 + i * 8, 14))}}>
                <div style={{fontFamily: GROTESK, fontWeight: 700, fontSize: 38, color: i === 2 ? BLUE.cyan : BLUE.ink}}>{big}</div>
                <div style={{fontFamily: MONO, fontSize: 16, color: BLUE.dim, letterSpacing: 2, marginTop: 4}}>{sub}</div>
              </Panel>
            ))}
          </div>
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 02 anatomy
const ANATOMY: [string, V3, string, string, 'left' | 'right'][] = [
  // part, model point at Z = 210, title, sub, label side (labels sit in two clean columns)
  ['mast', [0, -240, 470], 'Z lift', '2040 mast · lead screw', 'left'],
  ['camera', [-78, -115, 225], 'Vision', 'IMX708 120° camera', 'left'],
  ['power', [-80, -330, 100], 'Power', '4S 50.4 Wh · BMS', 'left'],
  ['yrail', [94, -180, 235], 'Y extractor', 'belt + finger servos', 'right'],
  ['tray', [-20, -110, 300], '2-slot tray', '45 mm = bay pitch', 'right'],
  ['electronics', [69, -312, 90], 'Compute', 'Pi 3 + motion board', 'right'],
  ['wheel_right', [137, AXLE_Y, 40], 'Drive', '2 × NEMA17 · direct', 'right'],
];

/** Stack labels of one column top to bottom, at least `gap` px apart, never above `top`. */
function column<T extends {y: number}>(items: T[], top: number, gap: number) {
  const sorted = [...items].sort((p, q) => p.y - q.y);
  let y = top - gap;
  return sorted.map((it) => {
    y = Math.max(it.y, y + gap);
    return {...it, ly: y};
  });
}

export const Anatomy: React.FC = () => (
  <Scene id="anatomy">
    {(f, a, b) => {
      const pts = ANATOMY.map(([part, m, title, sub, side], i) => ({...at(rp(m, f, part), f), part, title, sub, side, i}));
      const robotX = at(rp([0, -210, 300], f), f).x;
      const placed = [...column(pts.filter((q) => q.side === 'left'), 330, 120), ...column(pts.filter((q) => q.side === 'right'), 330, 110)];
      return (
        <>
          <div style={{position: 'absolute', left: 110, top: 90, width: 1100, ...inOut(f, a, b)}}>
            <Kicker n="02" text="Anatomy" at={a + 4} />
            <div style={{height: 20}} />
            <Headline text="Seven subsystems, *one 4.5 kg robot.*" at={a + 10} size={60} />
          </div>
          {placed.map((q) => (
            <Callout key={q.part} x={q.x} y={q.y} lx={q.side === 'left' ? robotX - 340 : robotX + 340} ly={q.ly} at={a + 70 + q.i * 6} until={a + 200}
              title={q.title} sub={q.sub} align={q.side === 'left' ? 'right' : 'left'} />
          ))}
          <div style={{position: 'absolute', left: 110, bottom: 80, fontFamily: MONO, fontSize: 19, letterSpacing: 3, color: BLUE.dim, ...inOut(f, a + 90, b)}}>
            300 × 360 MM FOOTPRINT · ≈ 545 MM TALL · ≈ 4.5 KG · V-SLOT + 3D-PRINTED PARTS
          </div>
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 03 drive
export const Drive: React.FC = () => (
  <Scene id="drive">
    {(f, a, b) => {
      const w = at(rp([149, AXLE_Y, 40], f), f);
      const spin = window01(f, a + 105, a + 232, 12);
      return (
        <>
          <Column f={f} a={a} b={b} n="03" kicker="Drive" title="Differential drive, *direct on the motor.*">
            <Specs at={a + 30} rows={[
              ['Motors', '2 × NEMA17 · TMC2209 drivers'],
              ['Wheels', 'Ø80 printed PETG hub + TPU tyre'],
              ['Speed', '150 mm/s cruise · 50 mm/s docking'],
              ['Step', '12.7 microsteps per mm of travel'],
            ]} />
            <div style={{height: 30}} />
            <Why at={a + 80} text="No belts, no gearbox: open-loop steps repeat, and all four axes share one driver type." />
          </Column>
          <Callout x={w.x} y={w.y} lx={w.x + 110} ly={w.y + 110} at={a + 50} until={a + 140} title="Wheel on the motor shaft" sub="5 mm D-shaft · set screw" />
          <div style={{position: 'absolute', right: 110, bottom: 90, opacity: spin}}>
            <Readout label="TURN IN PLACE" value="wheels counter-rotate" k={1} />
          </div>
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 04 lift + tray
export const Lift: React.FC = () => (
  <Scene id="lift">
    {(f, a, b) => {
      const s = stateAt(f);
      const pB = at(rp([-62, -40, s.Z + 12], f), f);
      const pA = at(rp([-62, -40, s.Z + 57], f), f);
      const k = window01(f, a + 40, b - 8, 12);
      return (
        <>
          <Column f={f} a={a} b={b} n="04" kicker="Z lift + 2-slot tray" title="One visit *pulls and inserts.*">
            <Specs at={a + 30} rows={[
              ['Mast', '2040 V-slot · 4 V-wheels'],
              ['Drive', 'NEMA17 + Tr8×2 lead screw'],
              ['Travel', 'Z 102 – 295 mm · 15 mm/s'],
              ['Holds', 'self-locking screw: load cannot drop'],
            ]} />
            <div style={{height: 30}} />
            <Why at={a + 90} text="Slot B takes the failed drive while slot A already carries the spare. The lift picks the slot, so no extra actuator." />
          </Column>
          <svg width={1920} height={1080} style={{position: 'absolute', inset: 0, opacity: k}}>
            <line x1={pB.x - 30} y1={pB.y} x2={pB.x - 30} y2={pA.y} stroke={BLUE.cyan} strokeWidth={2.5} />
            <line x1={pB.x - 42} y1={pB.y} x2={pB.x - 18} y2={pB.y} stroke={BLUE.cyan} strokeWidth={2.5} />
            <line x1={pA.x - 42} y1={pA.y} x2={pA.x - 18} y2={pA.y} stroke={BLUE.cyan} strokeWidth={2.5} />
            <text x={pB.x - 54} y={(pA.y + pB.y) / 2 + 8} textAnchor="end" fontFamily={GROTESK} fontWeight={700} fontSize={30} fill={BLUE.ink}>45 mm</text>
            <text x={pB.x - 54} y={(pA.y + pB.y) / 2 + 32} textAnchor="end" fontFamily={MONO} fontSize={15} fill={BLUE.dim}>= BAY PITCH</text>
            <text x={pA.x + 14} y={pA.y - 6} fontFamily={MONO} fontSize={17} fill={BLUE.cyan}>SLOT A · spare</text>
            <text x={pB.x + 14} y={pB.y + 22} fontFamily={MONO} fontSize={17} fill={BLUE.fault}>SLOT B · failed</text>
          </svg>
          <div style={{position: 'absolute', right: 110, bottom: 90, ...inOut(f, a + 50, b)}}>
            <Readout label="Z · SLOT B FLOOR" value={`${Math.round(s.Z)} mm`} k={1} />
          </div>
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 05 extractor
export const Extract: React.FC = () => (
  <Scene id="extract">
    {(f, a, b) => {
      const s = stateAt(f);
      const finger = at(robotToWorld([69.5, -187 + s.Y, s.Z + 15], s), f);
      const slotA = at(robotToWorld([0, -30, s.Z + 60], s), f);
      return (
        <>
          <Column f={f} a={a} b={b} n="05" kicker="Y extractor + fingers" title="Hook, pull, push. *No clamping.*">
            <Specs at={a + 30} rows={[
              ['Stroke', 'GT2 belt · 177 mm · 60 mm/s'],
              ['Grip', 'MG90S finger swings into the caddy notch'],
              ['Play', '10 mm finger in a 12 mm notch → ±1 mm'],
              ['Rack face', 'servos sit behind the finger: nothing passes it'],
            ]} />
            <div style={{height: 30}} />
            <Why at={a + 90} text="One mechanism pulls, pushes and holds the caddy while the robot drives." />
          </Column>
          <Callout x={finger.x} y={finger.y} lx={finger.x + 80} ly={finger.y - 150} at={a + 60} until={a + 320} title={s.fB > 0.5 ? 'Finger B · engaged' : 'Finger B · parked'} sub="MG90S servo · swings about y" />
          <div style={{position: 'absolute', right: 110, bottom: 90, display: 'flex', gap: 14, ...inOut(f, a + 50, b)}}>
            <Readout label="Y STROKE" value={`${Math.round(s.Y)} mm`} k={1} />
            <Readout label="FINGER B" value={s.fB > 0.5 ? 'ENGAGED' : 'PARKED'} k={1} color={s.fB > 0.5 ? BLUE.ok : BLUE.dim} />
          </div>
          <Callout x={slotA.x} y={slotA.y} lx={slotA.x + 90} ly={slotA.y - 120} at={a + 330} until={b - 8} title="Slot A now at bay 2" sub="lift 45 mm down · same visit" />
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 06 vision + docking
const Reticle: React.FC<{x: number; y: number; k: number; label: string}> = ({x, y, k, label}) => (
  <div style={{position: 'absolute', left: x - 50, top: y - 50, width: 100, height: 100, opacity: k}}>
    {[0, 1, 2, 3].map((c) => (
      <div key={c} style={{
        position: 'absolute', width: 24, height: 24, borderColor: BLUE.cyan, borderStyle: 'solid', borderWidth: 0,
        ...(c === 0 ? {left: 0, top: 0, borderLeftWidth: 3, borderTopWidth: 3} : c === 1 ? {right: 0, top: 0, borderRightWidth: 3, borderTopWidth: 3} : c === 2 ? {right: 0, bottom: 0, borderRightWidth: 3, borderBottomWidth: 3} : {left: 0, bottom: 0, borderLeftWidth: 3, borderBottomWidth: 3}),
      }} />
    ))}
    <div style={{position: 'absolute', left: 112, top: 30, fontFamily: MONO, fontSize: 17, color: BLUE.cyan, whiteSpace: 'nowrap', background: 'rgba(4,14,24,0.75)', padding: '4px 9px', borderRadius: 4}}>{label}</div>
  </div>
);

export const Vision: React.FC = () => (
  <Scene id="vision">
    {(f, a, b) => {
      const s = stateAt(f);
      const tag = at([TAG_APPROACH.x, TAG_APPROACH.y, TAG_APPROACH.z], f);
      const dist = Math.max(0, Math.round(s.cy - AXLE_Y));
      const docked = dist < 1;
      return (
        <>
          <Column f={f} a={a} b={b} n="06" kicker="Vision + docking" title="See the tag, *let the funnel finish.*">
            <Specs at={a + 30} rows={[
              ['Camera', 'IMX708 120° wide, on the tray'],
              ['Approach', 'AprilTag pose → steer into the dock'],
              ['Check', 'caddy tag ID must match the job'],
              ['Dock', 'V-funnel ±2 mm · nose switch'],
            ]} />
            <div style={{height: 30}} />
            <Why at={a + 90} text="Mechanical alignment instead of precise odometry: cheap, repeatable and easy to test." />
          </Column>
          {s.tag !== null && <Reticle x={tag.x} y={tag.y} k={ramp(f, a + 30, 10)} label="APRILTAG 0 · LOCKED" />}
          <div style={{position: 'absolute', right: 110, bottom: 90, display: 'flex', gap: 14, ...inOut(f, a + 40, b)}}>
            <Readout label="TO DOCK" value={docked ? 'DOCKED' : `${dist} mm`} k={1} color={docked ? BLUE.ok : BLUE.cyan} />
          </div>
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 07 power + electronics
export const Power: React.FC = () => (
  <Scene id="power">
    {(f, a, b) => {
      const mid = a + 300;
      const pi = at(rp([-80, -315, 95], f), f);
      const mb = at(rp([69, -312, 92], f), f);
      const bat = at(rp([-90, -350, 110], f), f);
      return (
        <>
          <Shade k={window01(f, a, b, 12)} width={68} />
          <div style={{position: 'absolute', left: 110, top: 90, width: 1100, ...inOut(f, a, b)}}>
            <Kicker n="07" text="Power + electronics" at={a + 4} />
            <div style={{height: 20}} />
            <Headline text="50 Wh, *fused, metered, E-stop safe.*" at={a + 10} size={58} />
          </div>
          <div style={{position: 'absolute', left: 110, top: 300, ...inOut(f, a + 20, mid + 10)}}>
            <PowerTree at={a + 24} />
          </div>
          <div style={{position: 'absolute', left: 110, top: 300, width: 760, ...inOut(f, mid, b)}}>
            <Specs at={mid + 6} rows={[
              ['Compute', 'Raspberry Pi 3: vision, mission, web dashboard'],
              ['Motion', 'ESP32-S3 + 4 × TMC2209 on our own PCB'],
              ['PCB', '100 × 100 mm, 2-layer, JLCPCB SMD assembly'],
              ['Energy', '≈ 0.6 – 1.0 Wh per swap · idle ≈ 4 W'],
            ]} width={760} />
            <div style={{height: 30}} />
            <Why at={mid + 50} width={760} text="Real-time stepping lives on the ESP32, everything smart on the Pi: each side does what it is good at." />
          </div>
          <Callout x={bat.x} y={bat.y} lx={bat.x + 120} ly={bat.y - 130} at={a + 120} until={mid} title="Battery 4S1P · 50.4 Wh" sub="under the 100 Wh cabin limit" />
          <Callout x={pi.x} y={pi.y} lx={pi.x + 140} ly={pi.y - 150} at={mid + 20} until={b - 6} title="Raspberry Pi 3" sub="USB serial to the motion board" />
          <Callout x={mb.x} y={mb.y} lx={mb.x + 160} ly={mb.y + 90} at={mid + 32} until={b - 6} title="Motion board RBG3" sub="ESP32-S3 · 4 × TMC2209" />
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 08 rack + safety
export const Safety: React.FC = () => (
  <Scene id="safety">
    {(f, a, b) => {
      const s = stateAt(f);
      const psu = at([-92, 202, 60], f);
      const ctl = at([-43, 182, 60], f);
      const lamp = at([60, 145, 415], f);
      const estop = s.light === 'red';
      return (
        <>
          <Column f={f} a={a} b={b} n="08" kicker="Rack + safety" title="The rack *keeps it safe.*">
            <Specs at={a + 30} rows={[
              ['Controller', 'ESP32 · Modbus TCP, same map as a Delta PLC'],
              ['Power', 'Delta 24 V DIN PSU, 120 W'],
              ['Dock', '24 V only while docked and E-stop OK'],
              ['Watchdog', 'robot silent 2 s → red lamp, dock off'],
              ['Robot', 'E-stop relay cuts motor power'],
            ]} />
          </Column>
          <Callout x={psu.x} y={psu.y} lx={psu.x + 130} ly={psu.y + 120} at={a + 50} until={b - 8} title="Delta 24 V PSU" sub="DRL-24V120W1EN" />
          <Callout x={ctl.x} y={ctl.y} lx={ctl.x + 170} ly={ctl.y - 70} at={a + 62} until={b - 8} title="Rack controller" sub="ESP32 · bays, dock, lamps" />
          <Callout x={lamp.x} y={lamp.y} lx={lamp.x + 120} ly={lamp.y - 110} at={a + 74} until={b - 8} title="Status lamps" sub="green idle · amber busy · red fault" color={estop ? BLUE.fault : BLUE.cyan} />
          {estop && (
            <div style={{position: 'absolute', right: 110, bottom: 90}}>
              <Panel style={{padding: '16px 22px', borderLeft: `4px solid ${BLUE.fault}`}}>
                <div style={{fontFamily: MONO, fontSize: 16, letterSpacing: 3, color: BLUE.fault}}>RACK E-STOP PRESSED</div>
                <div style={{fontFamily: INTER, fontWeight: 600, fontSize: 26, color: BLUE.ink, marginTop: 4}}>Dock power cut in hardware</div>
              </Panel>
            </div>
          )}
        </>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 09 full swap
const BAY_COLOR = {ok: BLUE.ok, new: BLUE.cyan, failed: BLUE.fault, empty: BLUE.amber} as const;
const BAY_LABEL = {ok: 'OK', new: 'NEW', failed: 'FAULT', empty: 'EMPTY'} as const;

export const Swap: React.FC = () => (
  <Scene id="swap">
    {(f, a, b) => {
      const s = stateAt(f);
      const k = window01(f, a, b, 10);
      const simT = Math.round(lerpNum(f, a + 42, MISSION_END, 0, 107));
      const clock = `${Math.floor(simT / 60)}:${String(simT % 60).padStart(2, '0')}`;
      const tagP = s.tag !== null ? at(s.tag === 0 ? [TAG_APPROACH.x, TAG_APPROACH.y, TAG_APPROACH.z] : spareToWorld([TAG_APPROACH.x, TAG_APPROACH.y, TAG_APPROACH.z]), f) : null;
      const led = at([-62, -4, H_BAY[1] + 34], f);
      const live = Math.floor(f / 15) % 2 === 0;
      return (
        <AbsoluteFill style={{opacity: k}}>
          <Shade k={0.62} width={32} />
          <div style={{position: 'absolute', left: 90, top: 70, display: 'flex', alignItems: 'center', gap: 14}}>
            <div style={{fontFamily: MONO, fontSize: 20, color: BLUE.bg, background: BLUE.cyan, padding: '3px 9px', borderRadius: 4, fontWeight: 600}}>09</div>
            <div style={{width: 12, height: 12, borderRadius: 6, background: BLUE.fault, opacity: live ? 1 : 0.3}} />
            <div style={{fontFamily: MONO, fontSize: 20, letterSpacing: 4, color: BLUE.ink}}>FULL SWAP · SIMULATED FROM CAD</div>
          </div>
          <div style={{position: 'absolute', left: 90, top: 150, width: 480}}>
            {STEPS.map((t, i) => {
              const st = stepStart(i);
              const done = s.step > i;
              const cur = s.step === i;
              const show = ramp(f, a + 4 + i * 3, 10);
              return (
                <div key={i} style={{display: 'flex', alignItems: 'center', gap: 16, height: 54, opacity: show * (cur ? 1 : done ? 0.6 : 0.38)}}>
                  <div style={{width: 4, height: 34, background: cur ? BLUE.cyan : 'transparent', borderRadius: 2}} />
                  <div style={{width: 30, fontFamily: MONO, fontSize: 18, color: done ? BLUE.ok : cur ? BLUE.cyan : BLUE.dim}}>{done ? '✓' : `0${i + 1}`}</div>
                  <div style={{fontFamily: INTER, fontWeight: cur ? 600 : 500, fontSize: cur ? 27 : 23, color: BLUE.ink, transform: `translateX(${cur ? ramp(f, st, 10) * 6 : 0}px)`}}>{t}</div>
                </div>
              );
            })}
          </div>
          <div style={{position: 'absolute', right: 90, top: 70, opacity: ramp(f, a + 6, 12)}}>
            <Panel style={{padding: '18px 22px', width: 300}}>
              <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: MONO, fontSize: 15, letterSpacing: 2, color: BLUE.dim}}>
                <span>RACK · MODBUS</span>
                <span style={{color: s.light === 'red' ? BLUE.fault : s.light === 'amber' ? BLUE.amber : BLUE.ok}}>● {s.light.toUpperCase()}</span>
              </div>
              {[3, 2, 1, 0].map((bb) => {
                const st = s.bays[bb];
                const blink = st === 'failed' && Math.floor(f / 8) % 2 === 0;
                return (
                  <div key={bb} style={{display: 'flex', alignItems: 'center', gap: 12, marginTop: 10, padding: '9px 12px', borderRadius: 8, background: 'rgba(120,190,255,0.05)', border: `1px solid ${st === 'ok' ? 'rgba(120,190,255,0.1)' : BAY_COLOR[st]}`}}>
                    <div style={{width: 10, height: 10, borderRadius: 5, background: BAY_COLOR[st], opacity: blink ? 0.3 : 1, boxShadow: `0 0 12px ${BAY_COLOR[st]}`}} />
                    <div style={{fontFamily: INTER, fontWeight: 600, fontSize: 20, color: BLUE.ink, flex: 1}}>Bay {bb + 1}</div>
                    <div style={{fontFamily: MONO, fontSize: 16, color: BAY_COLOR[st]}}>{BAY_LABEL[st]}</div>
                  </div>
                );
              })}
            </Panel>
          </div>
          <div style={{position: 'absolute', right: 90, bottom: 70, textAlign: 'right'}}>
            <div style={{fontFamily: MONO, fontSize: 17, color: BLUE.dim, letterSpacing: 3}}>MISSION CLOCK · SIM TIME</div>
            <div style={{fontFamily: GROTESK, fontWeight: 700, fontSize: 84, color: BLUE.ink, lineHeight: 1.05, fontVariantNumeric: 'tabular-nums'}}>{clock}</div>
            <div style={{fontFamily: MONO, fontSize: 17, color: BLUE.cyan}}>TARGET ≤ 3:00 PER SWAP</div>
          </div>
          <div style={{position: 'absolute', left: 90, bottom: 70, display: 'flex', flexDirection: 'column', gap: 10}}>
            {toasts(f).map((t) => {
              const kk = window01(f, t.f, t.f + 75, 8);
              const c = t.tone === 'ok' ? BLUE.ok : t.tone === 'warn' ? BLUE.fault : BLUE.blue;
              return (
                <Panel key={t.f} style={{padding: '12px 18px', opacity: kk, transform: `translateY(${(1 - kk) * 12}px)`, borderLeft: `3px solid ${c}`}}>
                  <div style={{fontFamily: MONO, fontSize: 20, color: BLUE.ink}}>{t.text}</div>
                </Panel>
              );
            })}
          </div>
          {tagP && <Reticle x={tagP.x} y={tagP.y} k={1} label={`APRILTAG ${s.tag} · LOCKED`} />}
          {f < stepStart(1) && <Callout x={led.x} y={led.y} lx={led.x + 150} ly={led.y - 130} at={a + 10} until={stepStart(1)} title="Bay 2 · SMART fault" sub="job queued by the dashboard" color={BLUE.fault} />}
        </AbsoluteFill>
      );
    }}
  </Scene>
);

// ---------------------------------------------------------------- 10 manufacturing
const MAKE: [string, string][] = [
  ['3D-printed parts', 'PETG · PLA · TPU, outside print service (400 mm bed)'],
  ['Frame', '2020 / 2040 V-slot, cut to length and drilled'],
  ['Motion PCB', 'JLCPCB 2-layer, SMD parts assembled'],
  ['Travel', '≈ 14 kg in 4 carry-on bags ≤ 7 kg'],
  ['Battery', '50.4 Wh, under the 100 Wh cabin limit'],
  ['Budget', '≈ USD 333 for the whole system'],
];

export const Make: React.FC = () => (
  <Scene id="make">
    {(f, a, b) => (
      <>
        <Shade k={window01(f, a, b, 12)} width={62} />
        <div style={{position: 'absolute', left: 110, top: 100, width: 1000, ...inOut(f, a, b)}}>
          <Kicker n="10" text="Built to travel" at={a + 4} />
          <div style={{height: 20}} />
          <Headline text="Printed, cut, *carried on.*" at={a + 10} size={60} />
        </div>
        <div style={{position: 'absolute', left: 110, top: 330, display: 'grid', gridTemplateColumns: 'repeat(2, 400px)', gap: 18, ...inOut(f, a, b)}}>
          {MAKE.map(([t, sub], i) => {
            const k = ease(ramp(f, a + 24 + i * 6, 14));
            return (
              <Panel key={i} style={{padding: '18px 22px', opacity: k, transform: `translateY(${(1 - k) * 18}px)`, borderTop: `2px solid ${i === 5 ? BLUE.cyan : 'rgba(120,190,255,0.25)'}`}}>
                <div style={{fontFamily: GROTESK, fontWeight: 700, fontSize: 28, color: i === 5 ? BLUE.cyan : BLUE.ink}}>{t}</div>
                <div style={{fontFamily: INTER, fontSize: 20, color: BLUE.dim, marginTop: 6, lineHeight: 1.35}}>{sub}</div>
              </Panel>
            );
          })}
        </div>
      </>
    )}
  </Scene>
);

// ---------------------------------------------------------------- close
const STATS: [string, string, string][] = [
  ['≤ 3 min', 'per full swap', 'target'],
  ['1:47', 'simulated cycle', 'base → rack → base'],
  ['≥ 95 %', 'success over 50 cycles', 'test target'],
  ['50.4 Wh', 'charges at its base', 'airline safe'],
  ['USD 333', 'whole system', 'robot + rack + station'],
  ['0 walks', 'per failed drive', 'lights-out ready'],
];

export const Close: React.FC = () => (
  <Scene id="close">
    {(f, a, b) => {
      const end = a + 92;
      const statsK = window01(f, a, end + 4, 10);
      const endK = ease(ramp(f, end, 16));
      return (
        <>
          <div style={{opacity: statsK}}>
            <Shade k={1} width={70} />
            <div style={{position: 'absolute', left: 110, top: 200, display: 'grid', gridTemplateColumns: 'repeat(3, 340px)', columnGap: 36, rowGap: 50}}>
              {STATS.map(([big, sub, note], i) => {
                const kk = ease(ramp(f, a + 4 + i * 5, 14));
                return (
                  <div key={i} style={{opacity: kk, transform: `translateY(${(1 - kk) * 22}px)`, borderTop: `1px solid ${BLUE.line}`, paddingTop: 20}}>
                    <div style={{fontFamily: GROTESK, fontWeight: 700, fontSize: 68, color: i === 5 ? BLUE.cyan : BLUE.ink, lineHeight: 1}}>{big}</div>
                    <div style={{fontFamily: INTER, fontSize: 24, color: BLUE.ink, marginTop: 10}}>{sub}</div>
                    <div style={{fontFamily: MONO, fontSize: 15, color: BLUE.dim, marginTop: 6, letterSpacing: 2, textTransform: 'uppercase'}}>{note}</div>
                  </div>
                );
              })}
            </div>
          </div>
          <AbsoluteFill style={{opacity: endK, background: `radial-gradient(ellipse at 50% 45%, ${BLUE.navy} 0%, ${BLUE.bg} 70%)`, alignItems: 'center', justifyContent: 'center'}}>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
              <div style={{fontFamily: GROTESK, fontWeight: 700, fontSize: 150, letterSpacing: 6, color: BLUE.ink, lineHeight: 1, transform: `scale(${1.04 - 0.04 * endK})`}}>CORVIN</div>
              <div style={{width: 360 * endK, height: 3, background: `linear-gradient(90deg, rgba(56,211,255,0), ${BLUE.cyan}, rgba(56,211,255,0))`, margin: '22px 0 26px'}} />
              <Headline text="Making drive replacement *easier.*" at={end + 8} size={50} style={{justifyContent: 'center'}} />
              <div style={{height: 34}} />
              <div style={{fontFamily: MONO, fontSize: 20, letterSpacing: 4, color: BLUE.dim, opacity: ramp(f, end + 24, 14)}}>BOYS GO TO THAILAND · BRAWIJAYA UNIVERSITY · DELTA CUP 2026</div>
            </div>
          </AbsoluteFill>
        </>
      );
    }}
  </Scene>
);

