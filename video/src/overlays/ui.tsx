// Motion-design primitives shared by the scene overlays.
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';
import {loadFont as loadGrotesk} from '@remotion/google-fonts/SpaceGrotesk';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS} from '../constants';

export const INTER = loadInter('normal', {weights: ['400', '500', '600'], subsets: ['latin']}).fontFamily;
export const GROTESK = loadGrotesk('normal', {weights: ['500', '700'], subsets: ['latin']}).fontFamily;
export const MONO = loadMono('normal', {weights: ['400', '600'], subsets: ['latin']}).fontFamily;

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** 0 -> 1 between f0 and f0 + d (clamped). */
export const ramp = (f: number, f0: number, d: number) => interpolate(f, [f0, f0 + d], [0, 1], clamp);
/** In at `a`, out at `b` (fade lengths `d`). */
export const window01 = (f: number, a: number, b: number, d = 12) => Math.min(ramp(f, a, d), 1 - ramp(f, b - d, d));

export const useSpring = (from: number, damping = 18) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - from, fps, config: {damping, mass: 0.6, stiffness: 140}});
};

export const Kicker: React.FC<{text: string; at: number; color?: string; style?: React.CSSProperties}> = ({text, at, color = COLORS.accent, style}) => {
  const f = useCurrentFrame();
  const k = ramp(f, at, 14);
  const chars = Math.round(text.length * ramp(f, at, 22));
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 14, opacity: k, ...style}}>
      <div style={{width: 36 * k, height: 3, background: color}} />
      <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 4, color, textTransform: 'uppercase', whiteSpace: 'nowrap'}}>
        {text.slice(0, chars)}
      </div>
    </div>
  );
};

/** Word-by-word slide-up reveal. Words wrapped in *stars* get the accent colour. */
export const Words: React.FC<{text: string; at: number; size?: number; stagger?: number; weight?: number; accent?: string; style?: React.CSSProperties; font?: string}> = ({
  text, at, size = 72, stagger = 3, weight = 700, accent = COLORS.accent, style, font = GROTESK,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', columnGap: size * 0.28, rowGap: 0, fontFamily: font, fontSize: size, fontWeight: weight, lineHeight: 1.08, color: COLORS.ink, letterSpacing: -0.02 * size, ...style}}>
      {text.split(' ').map((w, i) => {
        const s = spring({frame: f - at - i * stagger, fps, config: {damping: 20, mass: 0.5, stiffness: 160}});
        const hl = w.startsWith('*');
        const word = w.replace(/\*/g, '');
        return (
          <span key={i} style={{display: 'inline-block', overflow: 'hidden', paddingBottom: size * 0.08}}>
            <span style={{display: 'inline-block', transform: `translateY(${(1 - s) * 110}%)`, opacity: s, color: hl ? accent : undefined}}>{word}</span>
          </span>
        );
      })}
    </div>
  );
};

/** A leader line from a screen point (3D anchor) to a label box, drawn on. */
export const Callout: React.FC<{
  x: number; y: number; lx: number; ly: number; at: number; until: number; title: string; sub?: string; color?: string; align?: 'left' | 'right';
}> = ({x, y, lx, ly, at, until, title, sub, color = COLORS.accent, align = 'left'}) => {
  const f = useCurrentFrame();
  const k = window01(f, at, until, 10);
  const draw = ramp(f, at, 14);
  const txt = ramp(f, at + 8, 12);
  const elbowX = lx;
  const len1 = Math.hypot(elbowX - x, ly - y);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: k, pointerEvents: 'none'}}>
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <circle cx={x} cy={y} r={7 + 10 * (1 - draw)} fill="none" stroke={color} strokeWidth={2} opacity={draw} />
        <circle cx={x} cy={y} r={3.5} fill={color} />
        <line x1={x} y1={y} x2={x + (elbowX - x) * draw} y2={y + (ly - y) * draw} stroke={color} strokeWidth={2} strokeDasharray={`${len1}`} />
      </svg>
      <div
        style={{
          position: 'absolute', left: align === 'left' ? lx + 14 : undefined, right: align === 'right' ? 1920 - lx + 14 : undefined, top: ly - 26,
          opacity: txt, transform: `translateX(${(1 - txt) * (align === 'left' ? -12 : 12)}px)`, textAlign: align,
        }}
      >
        <div style={{fontFamily: GROTESK, fontWeight: 700, fontSize: 30, color: COLORS.ink, whiteSpace: 'nowrap', textShadow: '0 2px 12px rgba(0,0,0,0.9)'}}>{title}</div>
        {sub && <div style={{fontFamily: MONO, fontSize: 18, color: COLORS.dim, marginTop: 4, whiteSpace: 'nowrap'}}>{sub}</div>}
      </div>
    </div>
  );
};

export const Panel: React.FC<{style?: React.CSSProperties; children: React.ReactNode}> = ({style, children}) => (
  <div
    style={{
      background: 'rgba(14,17,22,0.72)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14,
      backdropFilter: 'blur(10px)', boxShadow: '0 20px 60px rgba(0,0,0,0.35)', ...style,
    }}
  >
    {children}
  </div>
);

export const Vignette: React.FC<{strength?: number}> = ({strength = 0.55}) => (
  <div style={{position: 'absolute', inset: 0, background: `radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,${strength}) 100%)`}} />
);

export const SideShade: React.FC<{k: number; side?: 'left' | 'right'; width?: number}> = ({k, side = 'left', width = 60}) => (
  <div
    style={{
      position: 'absolute', inset: 0, opacity: k,
      background: `linear-gradient(${side === 'left' ? 90 : 270}deg, rgba(8,10,13,0.92) 0%, rgba(8,10,13,0.75) ${width * 0.6}%, rgba(8,10,13,0) ${width}%)`,
    }}
  />
);
