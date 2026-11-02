// Headless check of the simulator core (no browser): runs swap jobs in both presets and asserts the invariants.
//   npm run check
import {Sim} from '../src/core/sim.ts';
import {Y_SAFE} from '../src/core/spec.ts';
import {PRESETS} from '../src/core/layout.ts';

let failures = 0;
const fail = (msg: string) => {
  failures++;
  console.error('  FAIL', msg);
};

// A caddy only moves with the robot or the Y carriage: per 0.1 s step at most drive 150 + Y 60 mm/s, plus the
// 2 mm z settle at a hand-off. Anything more is a jump on screen (e.g. snapping into the tray and back).
const MAX_STEP_MM = 30;
const lastPos = new Map<number, [number, number, number]>();

function invariants(sim: Sim, where: string) {
  for (const id of sim.world.loc.keys()) {
    const p = sim.caddyPos(id);
    const q = lastPos.get(id);
    if (p && q) {
      const d = Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]);
      if (d > MAX_STEP_MM) fail(`${where}: caddy ${id} jumped ${d.toFixed(0)} mm (${sim.world.name(sim.world.where(id))}, ${sim.mission.step})`);
    }
    if (p) lastPos.set(id, p);
    else lastPos.delete(id);
  }
  const r = sim.robot;
  if (r.Y > Y_SAFE && r.fA > 0 && r.fB > 0) fail(`${where}: both fingers engaged during a Y stroke (Y=${r.Y.toFixed(1)})`);
  const seen = new Set<string>();
  for (const [id, l] of sim.world.loc) {
    if (l.at === 'gone') continue;
    const k = l.at === 'tray' ? `tray${l.slot}` : `${l.st}:${l.i}`;
    if (seen.has(k)) fail(`${where}: two caddies at ${k} (caddy ${id})`);
    seen.add(k);
  }
}

function run(preset: keyof typeof PRESETS, faults: number, opts: {random?: boolean; estop?: boolean; block?: boolean} = {}) {
  const sim = new Sim(preset, 11);
  lastPos.clear();
  const racks = sim.world.racks;
  let injected = 0;
  let t = 0;
  const limit = 6 * 3600;
  let estopDone = false;
  let blockDone = false;
  if (opts.random) sim.setRandomFaults(true);
  while (t < limit) {
    const k = sim.kpis();
    const pending = [...sim.health.drives.values()].some((d) => d.ramp && sim.world.where(d.id)?.at === 'shelf' && (sim.world.where(d.id) as {st: string}).st !== 'home');
    if (!opts.random && injected < faults && sim.mission.job === null && k.queued === 0 && !pending) {
      const r = racks[injected % racks.length];
      sim.injectFault(r.id, (injected * 3) % 4);
      injected++;
    }
    if (opts.estop && !estopDone && sim.mission.state === 'EXTRACT_FAILED' && sim.robot.Y > 80) {
      sim.pressEstop();
      sim.advance(5);
      sim.releaseEstop();
      sim.advance(2);
      sim.resume();
      estopDone = true;
    }
    if (opts.block && !blockDone && sim.mission.step.startsWith('approach')) {
      sim.camBlocked = true;
      blockDone = true;
    }
    if (sim.mission.fault) {
      sim.camBlocked = false;
      sim.resume();
    }
    sim.advance(0.1);
    t += 0.1;
    invariants(sim, `${preset} t=${sim.t.toFixed(1)}`);
    if (!opts.random && sim.kpis().swaps >= faults) break;
    if (opts.random && sim.kpis().swaps >= faults) break;
  }
  const k = sim.kpis();
  const done = sim.jobs.filter((j) => j.status === 'done');
  console.log(
    `${preset.padEnd(5)} ${JSON.stringify(opts)}: ${k.swaps}/${faults} swaps in ${(sim.t / 60).toFixed(1)} sim-min · cycle ${k.cycle?.toFixed(1)} s · ` +
      `fault→insert ${k.window?.toFixed(1)} s · ${k.wh?.toFixed(3)} Wh/swap · clean ${((k.clean ?? 0) * 100).toFixed(0)} % · SOC ${(sim.battery.soc * 100).toFixed(1)} % · RMA shipped ${sim.rmaShipped}`,
  );
  if (k.swaps < faults) fail(`${preset}: only ${k.swaps}/${faults} swaps (state ${sim.mission.state}, step ${sim.mission.step})`);
  for (const j of done) {
    if (sim.world.where(j.failed!)?.at === 'shelf' && (sim.world.where(j.failed!) as {st: string}).st !== 'home') fail(`job ${j.id}: failed caddy still in a rack`);
    if (sim.jobs.some((o) => o.failed === j.fresh)) continue; // failed again later and was swapped out
    const l = sim.world.where(j.fresh!);
    if (!(l?.at === 'shelf' && l.st === j.rack && l.i === j.bay)) fail(`job ${j.id}: new caddy ${j.fresh} not in ${j.rack} bay ${j.bay + 1}`);
  }
  if (opts.estop && !estopDone) fail(`${preset}: E-stop scenario not exercised`);
  if (opts.block && !sim.logs.some((l) => l.msg.includes('backing off'))) fail(`${preset}: no back-off after blocking the camera`);
  return sim;
}

const arena = run('arena', 1);
const one = arena.jobs[0];
console.log('  arena cycle breakdown:', one.timeline.map((s) => `${s.state} ${(s.t1! - s.t0).toFixed(1)}s`).join(' · '));
run('arena', 10);
run('hall', 20);
run('hall', 3, {estop: true});
run('hall', 3, {block: true});
run('hall', 15, {random: true});
if (failures) {
  console.error(`${failures} failure(s)`);
  process.exit(1);
}
console.log('all checks passed');
