// Writes sfx-cues.csv (every sound cue of the technical film: frame, time, SFX id, length, volume, what it marks).
import {writeFileSync} from 'node:fs';
import {CUES} from './sfx';

const count: Record<string, number> = {};
for (const c of CUES) count[c.id] = (count[c.id] ?? 0) + 1;
console.log(CUES.length, JSON.stringify(count));
const t = (f: number) => `${Math.floor(f / 1800)}:${String(Math.floor((f / 30) % 60)).padStart(2, '0')}.${String(Math.round((f % 30) * 3.33)).padStart(2, '0')}`;
writeFileSync('sfx-cues.csv', ['frame,time,sfx_id,duration_frames,loop,volume,note', ...CUES.map((c) => `${c.f},${t(c.f)},${c.id},${c.dur ?? ''},${c.loop ? 'yes' : ''},${c.vol},"${c.note}"`)].join('\n') + '\n');
