import './style.css';
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {Sim} from './core/sim.ts';
import {PRESETS} from './core/layout.ts';
import {CAM_H, CAM_W, COLORS} from './core/spec.ts';
import {CAM_VFOV, detections} from './core/vision.ts';
import {SceneView, loadModels} from './view/scene.ts';
import {Dashboard} from './view/ui.ts';

type PresetId = keyof typeof PRESETS;
type CamMode = 'overview' | 'follow' | 'station';
const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;

const pref = {
  get(k: string) {
    try {
      return localStorage.getItem(`corvin-sim:${k}`);
    } catch {
      return null;
    }
  },
  set(k: string, v: string) {
    try {
      localStorage.setItem(`corvin-sim:${k}`, v);
    } catch {
      /* storage blocked: fine, it's only a convenience */
    }
  },
};

// --- renderers ------------------------------------------------------------------------------------------------------
const canvas = $<HTMLCanvasElement>('gl');
const renderer = new THREE.WebGLRenderer({canvas, antialias: true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const pipCanvas = $<HTMLCanvasElement>('pipGl');
const pipRenderer = new THREE.WebGLRenderer({canvas: pipCanvas, antialias: true});
pipRenderer.setPixelRatio(1);
pipRenderer.toneMapping = THREE.ACESFilmicToneMapping;
pipRenderer.outputColorSpace = THREE.SRGBColorSpace;
pipRenderer.setSize(CAM_W, CAM_H, false);

const camera = new THREE.PerspectiveCamera(40, 1, 0.02, 40);
const robotCam = new THREE.PerspectiveCamera(CAM_VFOV, CAM_W / CAM_H, 0.012, 20);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI / 2 - 0.05;
controls.minDistance = 0.25;
controls.maxDistance = 9;

function resize() {
  const v = $('view');
  const w = v.clientWidth;
  const h = v.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(1, h);
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe($('view'));

// --- state ------------------------------------------------------------------------------------------------------------
let sim: Sim;
let view: SceneView;
const dash = new Dashboard();
let speed = Number(pref.get('speed') ?? 4) || 4;
let camMode: CamMode = 'overview';
let lastRobot = new THREE.Vector3();

function start(preset: PresetId) {
  sim = new Sim(preset, (Date.now() & 0xffff) + 1);
  sim.auto = $<HTMLInputElement>('autoMode').checked;
  sim.autoRestock = $<HTMLInputElement>('autoRestock').checked;
  if ($<HTMLInputElement>('randomFaults').checked) sim.setRandomFaults(true);
  view.build(sim);
  dash.bind(sim);
  $('sceneNote').textContent = PRESETS[preset].note;
  for (const b of document.querySelectorAll<HTMLButtonElement>('#presetSeg button')) b.setAttribute('aria-pressed', String(b.dataset.preset === preset));
  setBlock(false);
  setCam('overview', true);
  pref.set('preset', preset);
}

// --- cameras ---------------------------------------------------------------------------------------------------------
function setCam(mode: CamMode, jump = false) {
  camMode = mode;
  for (const b of document.querySelectorAll<HTMLButtonElement>('.camseg button')) b.setAttribute('aria-pressed', String(b.dataset.cam === mode));
  const e = view.extent();
  const r = view.robotWorldPos();
  let pos: THREE.Vector3;
  let tgt: THREE.Vector3;
  if (mode === 'overview') {
    const span = Math.max(e.w, e.d * 1.4);
    tgt = new THREE.Vector3(e.cx, 0.12, e.cz);
    pos = new THREE.Vector3(e.cx - span * 0.5, span * 0.65 + 0.35, e.cz + span * 0.8 + 0.4);
  } else if (mode === 'follow') {
    tgt = r.clone();
    pos = r.clone().add(new THREE.Vector3(-0.9, 0.75, 1.1));
  } else {
    const id = sim.mission.job?.rack ?? (sim.mission.location && sim.mission.location !== 'home' ? sim.mission.location : sim.world.racks[0].id);
    tgt = view.stationWorldPos(id);
    tgt.y = 0.2;
    pos = tgt.clone().add(new THREE.Vector3(-0.75, 0.42, 1.0));
  }
  if (jump) {
    camera.position.copy(pos);
    controls.target.copy(tgt);
    flight = null;
  } else flight = {p0: camera.position.clone(), t0: controls.target.clone(), p1: pos, t1: tgt, k: 0};
  lastRobot = r.clone();
  controls.update();
}
let flight: {p0: THREE.Vector3; t0: THREE.Vector3; p1: THREE.Vector3; t1: THREE.Vector3; k: number} | null = null;

function updateCamera(dt: number) {
  if (flight) {
    flight.k = Math.min(1, flight.k + dt / 0.9);
    const e = flight.k < 0.5 ? 4 * flight.k ** 3 : 1 - (-2 * flight.k + 2) ** 3 / 2;
    camera.position.lerpVectors(flight.p0, flight.p1, e);
    controls.target.lerpVectors(flight.t0, flight.t1, e);
    if (flight.k >= 1) flight = null;
  } else if (camMode === 'follow') {
    // carry the camera along with the robot; the user can still orbit around it
    const r = view.robotWorldPos();
    const d = r.clone().sub(lastRobot);
    camera.position.add(d);
    controls.target.add(d);
    lastRobot = r;
  }
  if (camMode !== 'follow') lastRobot = view.robotWorldPos();
  controls.update();
}

// --- robot camera view -----------------------------------------------------------------------------------------------
const overlay = $<HTMLCanvasElement>('pipOverlay').getContext('2d')!;
let pipAcc = 0;
const KIND_COLOR = {approach: COLORS.green, shelf: COLORS.blue, caddy: COLORS.amber};

function renderPip(dt: number) {
  pipAcc += dt;
  if (pipAcc < 1 / 15) return; // ~15 fps, like a real camera stream
  pipAcc = 0;
  $('pipBlocked').hidden = !sim.camBlocked;
  if (!sim.camBlocked) {
    view.robotCamera(robotCam);
    pipRenderer.render(view.scene, robotCam);
  }
  overlay.clearRect(0, 0, CAM_W, CAM_H);
  if (!sim.camBlocked) view.robotCamera(robotCam);
  const dets = detections(sim.world, sim.robot.pose, sim.robot.Z, sim.camBlocked).filter((d) => d.kind === 'approach' || !view.occluded(robotCam, d.center));
  overlay.lineWidth = 3;
  overlay.font = '600 17px ui-monospace, Menlo, Consolas, monospace';
  for (const d of dets) {
    const col = KIND_COLOR[d.kind];
    overlay.strokeStyle = col;
    overlay.beginPath();
    d.px.forEach(([x, y], i) => (i ? overlay.lineTo(x, y) : overlay.moveTo(x, y)));
    overlay.closePath();
    overlay.stroke();
    const top = d.px.reduce((a, b) => (b[1] < a[1] ? b : a));
    const label = d.kind === 'caddy' ? `caddy ${d.id}` : d.kind === 'shelf' ? `shelf ${d.id}` : `tag ${d.id} · ${(d.dist / 10).toFixed(0)} cm`;
    const w = overlay.measureText(label).width + 10;
    overlay.fillStyle = 'rgba(0,0,0,0.65)';
    overlay.fillRect(top[0] - 4, top[1] - 28, w, 22);
    overlay.fillStyle = col;
    overlay.fillText(label, top[0] + 1, top[1] - 11);
  }
  const approaching = sim.mission.step.startsWith('approach');
  const p = approaching ? sim.lastTagPose : null;
  const cells: [string, string][] = p
    ? [['d', `${p.d.toFixed(0)} mm`], ['x', `${p.x.toFixed(1)} mm`], ['θ', `${p.theta.toFixed(1)}°`], ['ψ', `${p.psi.toFixed(1)}°`]]
    : [['tags', String(dets.length)], ['approach', dets.some((d) => d.kind === 'approach') ? 'in view' : '—'], ['shelf', String(dets.filter((d) => d.kind === 'shelf').length)], ['caddy', dets.find((d) => d.kind === 'caddy')?.id.toString() ?? '—']];
  const html = cells.map(([k, v]) => `<div><span>${k}</span>${v}</div>`).join('');
  if ($('pipHud').innerHTML !== html) $('pipHud').innerHTML = html;
}

// --- controls ---------------------------------------------------------------------------------------------------------
function setSpeed(s: number) {
  speed = s;
  pref.set('speed', String(s));
  for (const b of document.querySelectorAll<HTMLButtonElement>('#speedSeg button')) b.setAttribute('aria-pressed', String(Number(b.dataset.speed) === s));
}
function setBlock(on: boolean) {
  if (sim) sim.camBlocked = on;
  $('blockCam').setAttribute('aria-pressed', String(on));
  $('blockCam').textContent = on ? 'Unblock camera' : 'Block camera';
}

for (const b of document.querySelectorAll<HTMLButtonElement>('#speedSeg button')) b.addEventListener('click', () => setSpeed(Number(b.dataset.speed)));
for (const b of document.querySelectorAll<HTMLButtonElement>('#presetSeg button')) b.addEventListener('click', () => start(b.dataset.preset as PresetId));
for (const b of document.querySelectorAll<HTMLButtonElement>('.camseg button')) b.addEventListener('click', () => setCam(b.dataset.cam as CamMode));
$<HTMLInputElement>('autoMode').addEventListener('change', (e) => (sim.auto = (e.target as HTMLInputElement).checked));
$<HTMLInputElement>('autoRestock').addEventListener('change', (e) => (sim.autoRestock = (e.target as HTMLInputElement).checked));
$<HTMLInputElement>('randomFaults').addEventListener('change', (e) => sim.setRandomFaults((e.target as HTMLInputElement).checked));
$('restock').addEventListener('click', () => sim.restock());
$('blockCam').addEventListener('click', () => {
  setBlock(!sim.camBlocked);
  sim.log(sim.camBlocked ? 'warn' : 'info', 'operator', sim.camBlocked ? 'camera lens blocked' : 'camera lens cleared');
});
$('resume').addEventListener('click', () => sim.resume());
$('reset').addEventListener('click', () => start(sim.preset.id));
$('estop').addEventListener('click', () => (sim.estop ? sim.releaseEstop() : sim.pressEstop()));
$('pipSize').addEventListener('click', () => {
  const big = $('pip').classList.toggle('big');
  $('pipSize').setAttribute('aria-label', big ? 'Shrink camera view' : 'Enlarge camera view');
});
window.addEventListener('keydown', (e) => {
  if (e.target instanceof HTMLInputElement) return;
  if (e.code === 'Space') {
    e.preventDefault();
    sim.estop ? sim.releaseEstop() : sim.pressEstop();
  }
});

// click a drive in 3D to fail it
const ray = new THREE.Raycaster();
let down: {x: number; y: number} | null = null;
canvas.addEventListener('pointerdown', (e) => (down = {x: e.clientX, y: e.clientY}));
canvas.addEventListener('pointerup', (e) => {
  if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 4) return;
  const rect = canvas.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1), camera);
  const hit = ray.intersectObjects(view.pickables, true)[0];
  const id = hit?.object.userData.caddyId as number | undefined;
  if (id === undefined) return;
  const l = sim.world.where(id);
  if (l?.at === 'shelf' && l.st !== 'home') sim.injectFault(l.st, l.i);
});

// --- loop ---------------------------------------------------------------------------------------------------------------
let last = performance.now();
let uiAcc = 0;
function frame(now: number) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  requestAnimationFrame(frame); // first, so one bad frame can never stop the demo
  sim.advance(dt * speed);
  try {
    view.sync(now / 1000);
    updateCamera(dt);
    renderer.render(view.scene, camera);
    renderPip(dt);
  } catch (err) {
    console.error(err);
  }
  uiAcc += dt;
  if (uiAcc >= 0.2) {
    uiAcc = 0;
    dash.update();
  }
}

loadModels((k) => ($('loading').textContent = `Loading CAD models… ${Math.round(k * 100)} %`))
  .then((models) => {
    view = new SceneView(models, renderer);
    resize();
    setSpeed(speed);
    const p = pref.get('preset');
    start(p === 'arena' || p === 'hall' ? p : 'hall');
    $('loading').hidden = true;
    requestAnimationFrame(frame);
  })
  .catch((err) => {
    $('loading').textContent = `Could not load the CAD models: ${err}`;
    console.error(err);
  });
