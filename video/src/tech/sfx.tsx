// Sound layer of the technical film. Cues are derived from the script (motions, events, scene cuts) and keyed by
// the SFX ids of PLAN-corvin-150s.md §10. A cue plays only when a matching file exists: public/sfx/<id>*.wav|mp3
// (several files with the same id prefix rotate as variations). Music: the first file in public/music/.
import {Audio, getStaticFiles, interpolate, Sequence} from 'remotion';
import {Ch} from '../engine';
import {EVENTS, sampleChannel, TS, T_TOTAL} from './timeline';

export type Cue = {f: number; id: string; dur?: number; loop?: boolean; vol?: number; note: string};

const VOL: Record<string, number> = {
  sfx_01: 0.9, sfx_02: 0.45, sfx_03: 0.55, sfx_04: 0.3, sfx_05: 0.35, sfx_06: 0.3, sfx_07: 0.3, sfx_08: 0.55, sfx_09: 0.5,
  sfx_10: 0.35, sfx_11: 0.35, sfx_12: 0.35, sfx_13: 0.4, sfx_14: 0.45, sfx_15: 0.45, sfx_16: 0.55, sfx_17: 0.5, sfx_18: 0.55,
  sfx_19: 0.5, sfx_20: 0.2, sfx_21: 0.5, sfx_22: 0.6, sfx_23: 0.45, sfx_24: 0.35, sfx_25: 0.4, sfx_26: 0.45, sfx_27: 0.55,
  sfx_28: 0.15, sfx_29: 0.4, sfx_30: 0.45, sfx_31: 0.8,
};

/** Motion segments of a channel: [start, end] frames where it changes by more than eps per frame. */
function segments(c: Ch, eps: number, from = 0, to = T_TOTAL): [number, number][] {
  const out: [number, number][] = [];
  let s0 = -1;
  for (let f = from + 1; f <= to; f++) {
    const d = Math.abs(sampleChannel(c, f) - sampleChannel(c, f - 1));
    const moving = d > eps && d < 400; // jumps are cuts, not motion
    if (moving && s0 < 0) s0 = f - 1;
    if (!moving && s0 >= 0) {
      if (f - s0 > 2) out.push([s0, f]);
      s0 = -1;
    }
  }
  return out;
}

function build(): Cue[] {
  const c: Cue[] = [];
  const add = (f: number, id: string, note: string, dur?: number, loop?: boolean) => c.push({f: Math.round(f), id, note, dur, loop});
  const S = TS;
  // titles, transitions, accents
  add(S.intro[0] + 8, 'sfx_01', 'Corvin logo reveal');
  for (const k of Object.keys(S) as (keyof typeof S)[]) if (S[k][0] > 0) add(S[k][0] - 6, 'sfx_02', `transition → ${k}`);
  add(S.swap[0] - 75, 'sfx_03', 'riser into the full swap (2.5 s, ends on the cut)');
  add(S.anatomy[0] + 24, 'sfx_08', 'exploded view: parts separate');
  add(S.anatomy[0] + 196, 'sfx_09', 'parts snap back');
  add(S.make[0] + 6, 'sfx_08', 'flat-pack explode');
  add(S.make[0] + 140, 'sfx_09', 'parts snap back');
  add(S.close[0] + 92, 'sfx_31', 'end card');
  // UI: spec rows and callouts appearing
  for (const k of ['drive', 'lift', 'extract', 'vision', 'safety'] as const) for (let i = 0; i < 4; i++) add(S[k][0] + 30 + i * 6, 'sfx_04', `${k}: spec row ${i + 1}`);
  for (let i = 0; i < 3; i++) add(S.system[0] + 40 + i * 16, 'sfx_04', `system: callout ${i + 1}`);
  for (let i = 0; i < 7; i++) add(S.anatomy[0] + 70 + i * 6, 'sfx_04', `anatomy: label ${i + 1}`);
  add(S.system[0] + 110, 'sfx_24', 'Wi-Fi / Modbus link draws');
  add(S.system[0] + 150, 'sfx_07', 'job summary panels');
  add(S.make[0] + 24, 'sfx_07', 'manufacturing cards');
  add(S.swap[0] + 6, 'sfx_07', 'swap HUD panels');
  add(S.close[0] + 4, 'sfx_06', 'closing numbers');
  add(S.vision[0] + 30, 'sfx_05', 'camera scan / frustum');
  add(S.power[0] + 24, 'sfx_19', 'power tree powers up');
  add(S.power[0] + 60, 'sfx_20', 'energy flow hum', S.power[0] + 300 - (S.power[0] + 60), true);
  add(S.power[0] + 310, 'sfx_05', 'electronics close-up');
  // ambience on the floor scenes
  add(S.system[0], 'sfx_28', 'server room bed', S.system[1] - S.system[0], true);
  add(S.swap[0], 'sfx_28', 'server room bed', S.swap[1] - S.swap[0], true);
  add(S.make[0] + 20, 'sfx_29', '3D printer');
  add(S.make[0] + 110, 'sfx_30', 'packing / zipper');
  // mechanics, derived from the motion tracks
  // driving = any of cx / cy / th moving (merged), after the intro turntable
  const drive = [...segments('cx', 0.4, S.anatomy[0]), ...segments('cy', 0.4, S.anatomy[0]), ...segments('th', 0.002, S.anatomy[0])].sort((p, q) => p[0] - q[0]);
  const merged: [number, number][] = [];
  for (const [a, b] of drive) {
    const m = merged[merged.length - 1];
    if (m && a <= m[1] + 3) m[1] = Math.max(m[1], b);
    else merged.push([a, b]);
  }
  for (const [a, b] of merged) {
    add(a, 'sfx_11', 'drive start');
    add(a, 'sfx_10', 'stepper drive loop', b - a, true);
  }
  for (const [a, b] of segments('Z', 0.05)) add(a, 'sfx_12', 'Z lift (lead screw)', b - a, true);
  for (const [a, b] of segments('Y', 0.2)) add(a, 'sfx_13', 'Y belt stroke', b - a);
  for (const ch of ['fA', 'fB'] as const) for (const [a] of segments(ch, 0.01)) add(a, 'sfx_14', `servo ${ch === 'fA' ? 'A' : 'B'}`);
  // events
  for (const e of EVENTS) {
    if (e.kind === 'caddy' && e.to.mode === 'robot') add(e.f, 'sfx_15', 'caddy slides onto the tray');
    if (e.kind === 'caddy' && e.to.mode !== 'robot' && e.f > S.extract[0] && e.f < S.close[0]) add(e.f, 'sfx_16', 'caddy seated');
    if (e.kind === 'sfx' && e.id === 'dock') {
      add(e.f, 'sfx_18', 'funnel dock');
      add(e.f + 3, 'sfx_17', 'dock switch');
    }
    if (e.kind === 'sfx' && e.id === 'lock') add(e.f, 'sfx_25', 'caddy tag ID matches');
    if (e.kind === 'tag' && e.on) add(e.f, 'sfx_25', 'AprilTag locked');
    if (e.kind === 'sfx' && e.id === 'estop') {
      add(e.f, 'sfx_22', 'rack E-stop pressed');
      add(e.f + 4, 'sfx_21', 'dock relay drops');
    }
    if (e.kind === 'sfx' && e.id === 'charge') add(e.f, 'sfx_26', 'charging starts');
    if (e.kind === 'sfx' && e.id === 'done') add(e.f, 'sfx_27', 'job complete');
    if (e.kind === 'bay' && e.state === 'failed') add(e.f, 'sfx_23', 'bay 2 SMART fault');
  }
  return c.sort((p, q) => p.f - q.f).map((q) => ({...q, vol: VOL[q.id] ?? 0.4}));
}

export const CUES = build();

// Music edit (film frame -> track second): the track's bars sit 0.1 s in, so every segment starts 0.1 s late to put
// its downbeats on the film's 2 s cut grid. 0-96 s plays as is (calm intro, full section, start of the breakdown);
// 96-144 s jumps 8 s ahead so the second full section lands at 106 s, right before the swap; the close plays the
// track's own ending (192 s -> natural decay).
const MUSIC_EDIT: [number, number, number][] = [
  // film from, film to, track second at "film from"
  [0, 2880, 0.1],
  [2880, 4320, 104.1],
  [4320, T_TOTAL, 192.1],
];
const XF = 6; // crossfade frames at each edit
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const SfxLayer: React.FC = () => {
  const files = getStaticFiles();
  const sfx = files.filter((x) => x.name.startsWith('sfx/') && /\.(wav|mp3|ogg|m4a)$/i.test(x.name));
  const music = files.find((x) => x.name.startsWith('music/') && /\.(wav|mp3|ogg|m4a)$/i.test(x.name));
  const used: Record<string, number> = {};
  return (
    <>
      {music &&
        MUSIC_EDIT.map(([a, b, t], i) => {
          const last = i === MUSIC_EDIT.length - 1;
          const from = Math.max(0, a - (i ? XF : 0));
          const to = Math.min(T_TOTAL, b + (last ? 0 : XF));
          return (
            <Sequence key={`m${i}`} from={from} durationInFrames={to - from} layout="none" name={`music ${a}-${b}`}>
              <Audio
                src={music.src}
                startFrom={Math.round(t * 30) - (a - from)}
                volume={(fr) => {
                  const g = from + fr;
                  const fadeIn = i ? interpolate(g, [from, from + XF], [0, 1], clamp) : interpolate(g, [0, 24], [0, 1], clamp);
                  const fadeOut = last ? interpolate(g, [T_TOTAL - 30, T_TOTAL], [1, 0], clamp) : interpolate(g, [to - XF, to], [1, 0], clamp);
                  return 0.55 * fadeIn * fadeOut;
                }}
              />
            </Sequence>
          );
        })}
      {CUES.map((q, i) => {
        const opts = sfx.filter((x) => x.name.slice(4).startsWith(q.id));
        if (!opts.length) return null;
        const pick = opts[(used[q.id] = (used[q.id] ?? -1) + 1) % opts.length];
        const dur = q.dur ? Math.max(4, q.dur) : undefined;
        return (
          <Sequence key={i} from={q.f} durationInFrames={dur} layout="none" name={`${q.id} ${q.note}`}>
            <Audio src={pick.src} loop={q.loop} volume={q.vol} />
          </Sequence>
        );
      })}
    </>
  );
};
