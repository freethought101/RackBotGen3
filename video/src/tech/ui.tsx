// Motion-graphics building blocks of the technical film (blue look). Every animation is a function of the frame.
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {H, W} from '../constants';
import {project, V3} from '../geom';
import {GROTESK, INTER, MONO, ramp, window01} from '../overlays/ui';
import {techCameraAt} from './camera';
import {BLUE} from './theme';

export {GROTESK, INTER, MONO, ramp, window01};

/** Screen position of a world point (CAD mm) through the film camera at frame f. */
export const at = (p: V3, f: number) => project(p, techCameraAt(f), W, H);

const ease = (t: number) => 1 - Math.pow(1 - t, 3);

/** Show-in / show-out of a scene block: fade + a short rise in, fade + drift out. */
export function inOut(f: number, a: number, b: number, d = 14) {
  const i = ease(ramp(f, a, d));
  const o = ramp(f, b - d, d);
  return {opacity: i * (1 - o), transform: `translateY(${(1 - i) * 26 - o * 10}px)`};
}

export const Kicker: React.FC<{n?: string; text: string; at: number; color?: string}> = ({n, text, at: a, color = BLUE.cyan}) => {
  const f = useCurrentFrame();
  const k = ramp(f, a, 14);
  const chars = Math.round(text.length * ramp(f, a + 2, 20));
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 16, opacity: k}}>
      {n && <div style={{fontFamily: MONO, fontSize: 22, color: BLUE.bg, background: color, padding: '3px 9px', borderRadius: 4, fontWeight: 600}}>{n}</div>}
      <div style={{width: 40 * k, height: 2, background: color}} />
      <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 5, color, textTransform: 'uppercase', whiteSpace: 'nowrap'}}>{text.slice(0, chars)}</div>
    </div>
  );
};

/** Word-by-word slide-up headline; words in *stars* get the accent colour. */
export const Headline: React.FC<{text: string; at: number; size?: number; style?: React.CSSProperties; accent?: string}> = ({text, at: a, size = 64, style, accent = BLUE.cyan}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  let hl = false;
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', columnGap: size * 0.26, fontFamily: GROTESK, fontWeight: 700, fontSize: size, lineHeight: 1.06, color: BLUE.ink, letterSpacing: -0.02 * size, ...style}}>
      {text.split(' ').map((w, i) => {
        if (w.startsWith('*')) hl = true;
        const isHl = hl;
        if (w.endsWith('*')) hl = false;
        const s = spring({frame: f - a - i * 2.5, fps, config: {damping: 20, mass: 0.5, stiffness: 170}});
        return (
          <span key={i} style={{display: 'inline-block', overflow: 'hidden', paddingBottom: size * 0.1}}>
            <span style={{display: 'inline-block', transform: `translateY(${(1 - s) * 110}%)`, opacity: s, color: isHl ? accent : undefined}}>{w.replace(/\*/g, '')}</span>
          </span>
        );
      })}
    </div>
  );
};

export const Panel: React.FC<{style?: React.CSSProperties; children: React.ReactNode}> = ({style, children}) => (
  <div style={{background: BLUE.panel, border: `1px solid ${BLUE.line}`, borderRadius: 14, backdropFilter: 'blur(12px)', boxShadow: '0 24px 70px rgba(0,0,0,0.35)', ...style}}>{children}</div>
);

/** Spec table: label / value rows drawn in one after another. */
export const Specs: React.FC<{rows: [string, string][]; at: number; width?: number}> = ({rows, at: a, width = 640}) => {
  const f = useCurrentFrame();
  return (
    <div style={{width}}>
      {rows.map(([l, v], i) => {
        const k = ease(ramp(f, a + i * 6, 14));
        return (
          <div key={i} style={{display: 'flex', alignItems: 'baseline', gap: 20, padding: '13px 0', borderTop: `1px solid rgba(120,190,255,${0.22 * k})`, opacity: k, transform: `translateX(${(1 - k) * -18}px)`}}>
            <div style={{width: 150, flex: 'none', fontFamily: MONO, fontSize: 17, letterSpacing: 2.5, color: BLUE.dim, textTransform: 'uppercase'}}>{l}</div>
            <div style={{fontFamily: INTER, fontWeight: 500, fontSize: 25, color: BLUE.ink, lineHeight: 1.3}}>{v}</div>
          </div>
        );
      })}
    </div>
  );
};

/** The design reason: one sentence behind a "why" tab. */
export const Why: React.FC<{text: string; at: number; width?: number}> = ({text, at: a, width = 640}) => {
  const f = useCurrentFrame();
  const k = ease(ramp(f, a, 16));
  return (
    <div style={{width, opacity: k, transform: `translateY(${(1 - k) * 14}px)`, display: 'flex', gap: 18, alignItems: 'stretch'}}>
      <div style={{width: 4, borderRadius: 2, background: `linear-gradient(${BLUE.cyan}, ${BLUE.blue})`, flex: 'none'}} />
      <div>
        <div style={{fontFamily: MONO, fontSize: 16, letterSpacing: 4, color: BLUE.cyan, marginBottom: 6}}>WHY THIS DESIGN</div>
        <div style={{fontFamily: INTER, fontSize: 25, lineHeight: 1.42, color: BLUE.ink}}>{text}</div>
      </div>
    </div>
  );
};

/** A leader line from a projected 3D anchor to a label, drawn on. */
export const Callout: React.FC<{
  x: number; y: number; lx: number; ly: number; at: number; until: number; title: string; sub?: string; color?: string; align?: 'left' | 'right';
}> = ({x, y, lx, ly, at: a, until, title, sub, color = BLUE.cyan, align = 'left'}) => {
  const f = useCurrentFrame();
  const k = window01(f, a, until, 10);
  const draw = ease(ramp(f, a, 14));
  const txt = ramp(f, a + 8, 12);
  const end = align === 'left' ? lx + 120 : lx - 120;
  const len = Math.hypot(lx - x, ly - y) + 120;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: k, pointerEvents: 'none'}}>
      <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
        <circle cx={x} cy={y} r={8 + 12 * (1 - draw)} fill="none" stroke={color} strokeWidth={2} opacity={draw} />
        <circle cx={x} cy={y} r={4} fill={color} />
        <polyline points={`${x},${y} ${lx},${ly} ${end},${ly}`} fill="none" stroke={color} strokeWidth={2} strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
      </svg>
      <div
        style={{
          position: 'absolute', top: ly - 44, opacity: txt, textAlign: align,
          left: align === 'left' ? lx : undefined, right: align === 'right' ? W - lx : undefined,
          transform: `translateY(${(1 - txt) * 8}px)`,
        }}
      >
        <div style={{fontFamily: GROTESK, fontWeight: 700, fontSize: 28, color: BLUE.ink, whiteSpace: 'nowrap', textShadow: '0 2px 14px rgba(0,0,0,0.85)'}}>{title}</div>
        {sub && <div style={{fontFamily: MONO, fontSize: 17, color: BLUE.dim, marginTop: 30, whiteSpace: 'nowrap', textShadow: '0 2px 10px rgba(0,0,0,0.9)'}}>{sub}</div>}
      </div>
    </div>
  );
};

/** A live readout chip (value updates every frame). */
export const Readout: React.FC<{label: string; value: string; k: number; color?: string}> = ({label, value, k, color = BLUE.cyan}) => (
  <Panel style={{padding: '12px 18px', opacity: k, minWidth: 190}}>
    <div style={{fontFamily: MONO, fontSize: 15, letterSpacing: 3, color: BLUE.dim}}>{label}</div>
    <div style={{fontFamily: GROTESK, fontWeight: 700, fontSize: 40, color, lineHeight: 1.1, fontVariantNumeric: 'tabular-nums'}}>{value}</div>
  </Panel>
);

/** Darkens one side of the frame so text reads over the 3D. */
export const Shade: React.FC<{k: number; side?: 'left' | 'right'; width?: number}> = ({k, side = 'left', width = 58}) => (
  <div
    style={{
      position: 'absolute', inset: 0, opacity: k,
      background: `linear-gradient(${side === 'left' ? 90 : 270}deg, rgba(4,14,24,0.94) 0%, rgba(4,14,24,0.78) ${width * 0.6}%, rgba(4,14,24,0) ${width}%)`,
    }}
  />
);

export const lerpNum = (f: number, a: number, b: number, v0: number, v1: number) =>
  interpolate(f, [a, b], [v0, v1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
