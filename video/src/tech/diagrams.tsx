// Animated power tree (spec 02 §1): nodes draw in one after another, edges carry moving energy dashes.
import {useCurrentFrame} from 'remotion';
import {BLUE} from './theme';
import {GROTESK, MONO, ramp} from './ui';

type Node = {id: string; x: number; y: number; title: string; sub: string; tone?: 'charge' | 'safety' | 'logic'};
const NW = 210;
const NH = 84;
const NODES: Node[] = [
  {id: 'dock', x: 0, y: 0, title: 'Dock 24 V', sub: 'Delta PSU · base', tone: 'charge'},
  {id: 'ss54', x: 250, y: 0, title: 'SS54 diode', sub: 'no back-feed', tone: 'charge'},
  {id: 'chg', x: 500, y: 0, title: 'CC/CV charger', sub: '16.8 V · 1.5 A', tone: 'charge'},
  {id: 'bat', x: 0, y: 150, title: 'Battery 4S1P', sub: '18650 · 50.4 Wh'},
  {id: 'bms', x: 250, y: 150, title: 'BMS · fuse', sub: '7.5 A at P+'},
  {id: 'ina', x: 500, y: 150, title: 'INA226', sub: 'Wh per swap'},
  {id: 'bus', x: 750, y: 150, title: 'VBAT bus', sub: '12 – 16.8 V'},
  {id: 'estop', x: 750, y: 300, title: 'E-stop relay', sub: 'cuts motor power', tone: 'safety'},
  {id: 'tmc', x: 750, y: 450, title: '4 × TMC2209', sub: '→ 4 × NEMA17'},
  {id: 'b58', x: 500, y: 450, title: 'Buck 5.8 V', sub: '→ 2 × MG90S'},
  {id: 'b515', x: 500, y: 300, title: 'Buck 5.15 V', sub: 'logic supply', tone: 'logic'},
  {id: 'pi', x: 250, y: 300, title: 'Raspberry Pi 3', sub: 'vision · mission · web', tone: 'logic'},
  {id: 'esp', x: 0, y: 300, title: 'ESP32-S3', sub: 'motion board', tone: 'logic'},
];
// edges: from, to, order (draw sequence), kind
const EDGES: [string, string, number, 'power' | 'charge' | 'data'][] = [
  ['bat', 'bms', 0, 'power'], ['bms', 'ina', 1, 'power'], ['ina', 'bus', 2, 'power'],
  ['bus', 'estop', 3, 'power'], ['estop', 'tmc', 4, 'power'], ['estop', 'b58', 4, 'power'],
  ['bus', 'b515', 5, 'power'], ['b515', 'pi', 6, 'power'], ['pi', 'esp', 7, 'data'],
  ['dock', 'ss54', 8, 'charge'], ['ss54', 'chg', 9, 'charge'], ['chg', 'bus', 10, 'charge'],
];
const byId = Object.fromEntries(NODES.map((n) => [n.id, n]));
const ORDER: Record<string, number> = {bat: 0, bms: 1, ina: 2, bus: 3, estop: 4, tmc: 5, b58: 5, b515: 6, pi: 7, esp: 8, dock: 9, ss54: 10, chg: 11};

function port(a: Node, b: Node): [number, number, number, number] {
  const ax = a.x + NW / 2;
  const ay = a.y + NH / 2;
  const bx = b.x + NW / 2;
  const by = b.y + NH / 2;
  if (Math.abs(ay - by) < 1) return ax < bx ? [a.x + NW, ay, b.x, by] : [a.x, ay, b.x + NW, by];
  if (Math.abs(ax - bx) < 1) return ay < by ? [ax, a.y + NH, bx, b.y] : [ax, a.y, bx, b.y + NH];
  return ay < by ? [ax, a.y + NH, bx, b.y] : [ax, a.y, bx, b.y + NH];
}

export const PowerTree: React.FC<{at: number; step?: number}> = ({at: a, step = 7}) => {
  const f = useCurrentFrame();
  const col = (t?: Node['tone']) => (t === 'charge' ? BLUE.ok : t === 'safety' ? BLUE.fault : t === 'logic' ? BLUE.blue : BLUE.cyan);
  return (
    <svg width={960} height={540} viewBox="-4 -4 968 548" style={{overflow: 'visible'}}>
      {EDGES.map(([from, to, o, kind], i) => {
        const [x1, y1, x2, y2] = port(byId[from], byId[to]);
        const k = ramp(f, a + 8 + o * step, 12);
        const midY = (y1 + y2) / 2;
        const d = Math.abs(y1 - y2) < 1 || Math.abs(x1 - x2) < 1 ? `M${x1},${y1} L${x2},${y2}` : `M${x1},${y1} L${x1},${midY} L${x2},${midY} L${x2},${y2}`;
        const c = kind === 'charge' ? BLUE.ok : kind === 'data' ? BLUE.blue : BLUE.cyan;
        return (
          <g key={i} opacity={k}>
            <path d={d} fill="none" stroke={c} strokeOpacity={0.25} strokeWidth={6} />
            <path d={d} fill="none" stroke={c} strokeWidth={2.5} strokeDasharray="10 12" strokeDashoffset={-(f - a) * (kind === 'data' ? 1.2 : 2.2)} />
            {kind === 'data' && <text x={(x1 + x2) / 2} y={y1 - 10} textAnchor="middle" fontFamily={MONO} fontSize={15} fill={BLUE.blue}>USB serial</text>}
          </g>
        );
      })}
      {NODES.map((n) => {
        const k = ramp(f, a + ORDER[n.id] * step, 12);
        const c = col(n.tone);
        return (
          <g key={n.id} opacity={k} transform={`translate(${n.x}, ${n.y + (1 - k) * 12})`}>
            <rect width={NW} height={NH} rx={12} fill="rgba(8,26,42,0.9)" stroke={c} strokeOpacity={0.75} strokeWidth={1.5} />
            <rect width={5} height={NH - 24} x={0} y={12} rx={2} fill={c} />
            <text x={20} y={36} fontFamily={GROTESK} fontWeight={700} fontSize={23} fill={BLUE.ink}>{n.title}</text>
            <text x={20} y={63} fontFamily={MONO} fontSize={15} fill={BLUE.dim}>{n.sub}</text>
          </g>
        );
      })}
    </svg>
  );
};
