// three.js view of a Sim: the real CAD meshes (exported for the pitch film, video/public/models) placed by the
// simulator state every frame. Assembly offsets follow video/src/three/World.tsx.
import * as THREE from 'three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';
import robotBaseUrl from '../../../video/public/models/robot_base.glb?url';
import robotLiftUrl from '../../../video/public/models/robot_lift.glb?url';
import robotExtUrl from '../../../video/public/models/robot_extractor.glb?url';
import fingerUrl from '../../../video/public/models/finger.glb?url';
import caddyUrl from '../../../video/public/models/caddy.glb?url';
import rackUrl from '../../../video/public/models/rack.glb?url';
import spareUrl from '../../../video/public/models/spare.glb?url';
import {AXLE_Y, BAY_PITCH, CAM_LENS, COLORS, FINGER_DZ, FINGER_X, RACK_TOP_Z, SPARE_TOP_Z, TAG_APPROACH, TAG_BAY, TAG_CADDY, TAG_FACE_Y, TOWER, Y_NOTCH_HOME, Y_PULL} from '../core/spec.ts';
import type {Sim} from '../core/sim.ts';
import type {Station} from '../core/layout.ts';
import {tagTexture} from './tag.ts';

/** CAD mm (x, y, z up) -> three.js m (y up). */
export const c3 = (x: number, y: number, z: number): [number, number, number] => [x / 1000, z / 1000, -y / 1000];

const URLS = {robot_base: robotBaseUrl, robot_lift: robotLiftUrl, robot_extractor: robotExtUrl, finger: fingerUrl, caddy: caddyUrl, rack: rackUrl, spare: spareUrl};
type ModelName = keyof typeof URLS;

export async function loadModels(onProgress?: (k: number) => void) {
  const loader = new GLTFLoader();
  const names = Object.keys(URLS) as ModelName[];
  let n = 0;
  const out = {} as Record<ModelName, THREE.Object3D>;
  await Promise.all(
    names.map(async (name) => {
      // The single-file build inlines each mesh as a data: URI; decode it here instead of fetching it, so the
      // page also works where fetch() of data: URIs is blocked.
      const url = URLS[name];
      const g = url.startsWith('data:')
        ? await loader.parseAsync(Uint8Array.from(atob(url.slice(url.indexOf(',') + 1)), (c) => c.charCodeAt(0)).buffer, '')
        : await loader.loadAsync(url);
      out[name] = g.scene;
      onProgress?.(++n / names.length);
    }),
  );
  return out;
}

type Models = Awaited<ReturnType<typeof loadModels>>;

function cloneModel(src: THREE.Object3D, ownMaterials = false) {
  const s = src.clone(true);
  s.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    m.castShadow = true;
    m.receiveShadow = true;
    if (ownMaterials) {
      const mats = (Array.isArray(m.material) ? m.material : [m.material]).map((x) => {
        const c = (x as THREE.MeshStandardMaterial).clone();
        c.emissive = new THREE.Color(COLORS.red);
        c.emissiveIntensity = 0;
        return c;
      });
      m.material = Array.isArray(m.material) ? mats : mats[0];
    }
  });
  return s;
}

function setEmissive(obj: THREE.Object3D, k: number) {
  obj.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    for (const mat of Array.isArray(m.material) ? m.material : [m.material]) (mat as THREE.MeshStandardMaterial).emissiveIntensity = k;
  });
}

const tagCache = new Map<number, THREE.Texture>();
function tagMesh(id: number, size: number, at: [number, number, number]) {
  if (!tagCache.has(id)) tagCache.set(id, tagTexture(id));
  const m = new THREE.Mesh(new THREE.PlaneGeometry(size / 1000, size / 1000), new THREE.MeshBasicMaterial({map: tagCache.get(id)!, toneMapped: false}));
  m.position.set(...c3(...at));
  m.userData.noOcclude = true;
  return m;
}

function glow(color: string, size: [number, number, number]) {
  return new THREE.Mesh(new THREE.BoxGeometry(...size), new THREE.MeshStandardMaterial({color, emissive: color, emissiveIntensity: 2, toneMapped: false}));
}

/** A camera-facing text label (canvas sprite) that can be redrawn. */
class Label {
  sprite: THREE.Sprite;
  private canvas = document.createElement('canvas');
  private tex: THREE.CanvasTexture;
  private last = '';
  constructor(h = 0.05) {
    this.canvas.width = 512;
    this.canvas.height = 128;
    this.tex = new THREE.CanvasTexture(this.canvas);
    this.tex.colorSpace = THREE.SRGBColorSpace;
    this.sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: this.tex, depthWrite: false, toneMapped: false, transparent: true}));
    this.sprite.scale.set(h * 4, h, 1);
    this.sprite.renderOrder = 10;
    this.sprite.userData.noOcclude = true;
  }
  set(title: string, sub: string, color: string) {
    const key = title + sub + color;
    if (key === this.last) return;
    this.last = key;
    const g = this.canvas.getContext('2d')!;
    g.clearRect(0, 0, 512, 128);
    g.fillStyle = 'rgba(11,13,16,0.82)';
    g.beginPath();
    g.roundRect(8, 8, 496, 112, 18);
    g.fill();
    g.fillStyle = color;
    g.fillRect(8, 8, 10, 112);
    g.fillStyle = COLORS.ink;
    g.font = '600 50px system-ui, -apple-system, Segoe UI, sans-serif';
    g.fillText(title, 40, 62);
    g.fillStyle = color;
    g.font = '500 34px system-ui, -apple-system, Segoe UI, sans-serif';
    g.fillText(sub, 40, 104);
    this.tex.needsUpdate = true;
  }
}

type StationView = {st: Station; group: THREE.Group; leds: THREE.Mesh[]; lamps: THREE.Mesh[]; label: Label};

export class SceneView {
  scene = new THREE.Scene();
  models: Models;
  sim!: Sim;
  private root = new THREE.Group();
  private stations = new Map<string, StationView>();
  private caddies = new Map<number, THREE.Object3D>();
  private robot!: {outer: THREE.Group; inner: THREE.Group; lift: THREE.Object3D; ext: THREE.Object3D; fA: THREE.Object3D; fB: THREE.Object3D; light: THREE.PointLight};
  private route!: THREE.Line;
  private routeKey = '';
  private target!: THREE.Mesh;
  private key!: THREE.DirectionalLight;
  pickables: THREE.Object3D[] = [];

  constructor(models: Models, renderer: THREE.WebGLRenderer) {
    this.models = models;
    const pm = new THREE.PMREMGenerator(renderer);
    this.scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environmentIntensity = 0.55;
    this.scene.add(this.root);
  }

  /** (Re)build everything for a sim (preset switch or reset). */
  build(sim: Sim) {
    this.sim = sim;
    this.root.clear();
    this.stations.clear();
    this.caddies.clear();
    this.pickables = [];
    const hall = sim.preset.id === 'hall';
    const bg = hall ? '#07090C' : COLORS.bg;
    this.scene.background = new THREE.Color(bg);
    this.scene.fog = new THREE.Fog(bg, hall ? 3.5 : 3, hall ? 9 : 8);

    // lights
    this.root.add(new THREE.HemisphereLight('#dfe8ff', '#1a1c20', hall ? 0.35 : 0.5));
    const ext = this.extent();
    const key = new THREE.DirectionalLight('#ffffff', hall ? 1.7 : 2.1);
    key.position.set(ext.cx + 1.2, 2.6, ext.cz + 1.8);
    key.target.position.set(ext.cx, 0, ext.cz);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    const half = Math.max(ext.w, ext.d) / 2 + 0.6;
    Object.assign(key.shadow.camera, {left: -half, right: half, top: half, bottom: -half, near: 0.5, far: 8});
    key.shadow.bias = -0.0004;
    this.key = key;
    this.root.add(key, key.target);
    const rim = new THREE.DirectionalLight('#7fb2ff', hall ? 1.0 : 1.1);
    rim.position.set(ext.cx - 1.5, 1.0, ext.cz - 1.4);
    this.root.add(rim);

    // floor
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.MeshStandardMaterial({color: hall ? '#0d1014' : '#121419', roughness: 0.92, map: this.floorTexture(hall)}));
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.root.add(floor);
    if (hall) this.root.add(this.hallDressing());

    for (const st of sim.world.stations) this.addStation(st);
    for (const id of sim.world.loc.keys()) this.caddyObj(id);
    this.addRobot();

    // planned route + target ring
    this.route = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineDashedMaterial({color: COLORS.accent, dashSize: 0.04, gapSize: 0.025, transparent: true, opacity: 0.9}));
    this.route.renderOrder = 5;
    this.route.userData.noOcclude = true;
    this.target = new THREE.Mesh(new THREE.RingGeometry(0.035, 0.05, 40), new THREE.MeshBasicMaterial({color: COLORS.accent, transparent: true, opacity: 0.9, toneMapped: false}));
    this.target.rotation.x = -Math.PI / 2;
    this.routeKey = '';
    this.root.add(this.route, this.target);
  }

  /** Layout bounds in three.js metres (x, z). */
  extent() {
    const xs = this.sim.world.stations.map((s) => s.x / 1000);
    const zs = this.sim.world.stations.map((s) => -s.y / 1000);
    const [x0, x1, z0, z1] = [Math.min(...xs), Math.max(...xs), Math.min(...zs), Math.max(...zs)];
    return {cx: (x0 + x1) / 2, cz: (z0 + z1) / 2, w: x1 - x0 + 0.6, d: z1 - z0 + 0.6};
  }

  private floorTexture(hall: boolean) {
    const c = document.createElement('canvas');
    c.width = c.height = 256;
    const g = c.getContext('2d')!;
    g.fillStyle = '#ffffff';
    g.fillRect(0, 0, 256, 256);
    g.strokeStyle = hall ? '#9aa3ad' : '#c9ced6';
    g.lineWidth = hall ? 3 : 1.5;
    g.strokeRect(0, 0, 256, 256);
    if (hall) {
      // perforated raised-floor tile look
      g.fillStyle = '#c4cad2';
      for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) g.fillRect(40 + i * 23, 40 + j * 23, 6, 6);
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    const tile = hall ? 0.3 : 0.1; // m per tile (hall tiles drawn at the robot's scale)
    t.repeat.set(30 / tile, 30 / tile);
    t.anisotropy = 8;
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }

  /** Background rows of rack silhouettes with blinking LEDs: the "data hall" around the working row. */
  private hallDressing() {
    const g = new THREE.Group();
    const c = document.createElement('canvas');
    c.width = 64;
    c.height = 128;
    const x = c.getContext('2d')!;
    x.fillStyle = '#000';
    x.fillRect(0, 0, 64, 128);
    for (let i = 0; i < 10; i++) {
      x.fillStyle = '#0a0d11';
      x.fillRect(4, 6 + i * 12, 56, 9);
      x.fillStyle = Math.random() > 0.12 ? '#3DDC84' : '#5AA9FF';
      x.fillRect(8, 9 + i * 12, 3, 3);
      if (Math.random() > 0.5) x.fillRect(14, 9 + i * 12, 3, 3);
    }
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    const face = new THREE.MeshStandardMaterial({color: '#15191f', emissive: '#ffffff', emissiveMap: tex, emissiveIntensity: 1.2, roughness: 0.6, metalness: 0.3});
    const side = new THREE.MeshStandardMaterial({color: '#12161b', roughness: 0.7, metalness: 0.4});
    const geo = new THREE.BoxGeometry(0.24, RACK_TOP_Z / 1000, 0.17);
    const mats = [side, side, side, side, face, face];
    const rows = [-0.75, -1.5, 2.15, 2.9]; // three z (= −CAD y) of the rows: behind the working row, and behind home at z=1.4
    for (const z of rows) {
      for (let i = -3; i <= 6; i++) {
        const m = new THREE.Mesh(geo, mats);
        m.position.set(i * 0.5, RACK_TOP_Z / 2000, z);
        m.castShadow = true;
        m.receiveShadow = true;
        g.add(m);
      }
    }
    // working row extends to both sides with idle racks
    for (const i of [-2, -1, 4, 5]) {
      const m = new THREE.Mesh(geo, mats);
      m.position.set(i * 0.5, RACK_TOP_Z / 2000, -0.075);
      g.add(m);
    }
    // overhead cable trays
    const tray = new THREE.MeshStandardMaterial({color: '#2a313b', metalness: 0.6, roughness: 0.5});
    for (const z of [-0.08, 1.48]) {
      const t = new THREE.Mesh(new THREE.BoxGeometry(5.5, 0.012, 0.1), tray);
      t.position.set(0.75, 0.62, z);
      g.add(t);
    }
    return g;
  }

  private addStation(st: Station) {
    const group = new THREE.Group();
    group.position.set(...c3(st.x, st.y, 0));
    group.rotation.y = st.phi;
    group.add(cloneModel(st.kind === 'rack' ? this.models.rack : this.models.spare));
    group.add(tagMesh(st.tag, TAG_APPROACH.size, [TAG_APPROACH.x, TAG_FACE_Y - 0.2, TAG_APPROACH.z]));
    const leds: THREE.Mesh[] = [];
    st.shelves.forEach((h, i) => {
      group.add(tagMesh(st.kind === 'rack' ? i + 1 : 11 + i, TAG_BAY.size, [TAG_BAY.x, TAG_FACE_Y - 0.2, h + TAG_BAY.dz]));
      const led = glow(COLORS.green, [0.006, 0.006, 0.003]);
      led.position.set(...c3(-62, -4, h + 34));
      group.add(led);
      leds.push(led);
    });
    const lamps: THREE.Mesh[] = [];
    if (st.kind === 'rack') {
      const seg = (TOWER.z1 - TOWER.z0) / 3;
      [COLORS.green, COLORS.amber, COLORS.red].forEach((col, i) => {
        const m = new THREE.Mesh(
          new THREE.CylinderGeometry((TOWER.r + 0.8) / 1000, (TOWER.r + 0.8) / 1000, (seg - 3) / 1000, 24),
          new THREE.MeshStandardMaterial({color: col, emissive: col, emissiveIntensity: 0.08, transparent: true, opacity: 0.92, toneMapped: false}),
        );
        m.position.set(...c3(TOWER.x, TOWER.y, TOWER.z0 + seg * (i + 0.5)));
        group.add(m);
        lamps.push(m);
      });
    }
    const label = new Label(st.kind === 'rack' ? 0.05 : 0.055);
    label.sprite.position.set(...c3(0, 60, (st.kind === 'rack' ? TOWER.z1 : SPARE_TOP_Z) + 70));
    group.add(label.sprite);
    this.root.add(group);
    this.stations.set(st.id, {st, group, leds, lamps, label});
  }

  private caddyObj(id: number) {
    let o = this.caddies.get(id);
    if (!o) {
      o = cloneModel(this.models.caddy, true);
      const tag = tagMesh(id, TAG_CADDY.size, [TAG_CADDY.x, TAG_CADDY.y, TAG_CADDY.dz]);
      o.add(tag);
      o.userData.caddyId = id;
      o.traverse((c) => (c.userData.caddyId = id));
      this.caddies.set(id, o);
      this.pickables.push(o);
    }
    return o;
  }

  private addRobot() {
    const outer = new THREE.Group();
    const inner = new THREE.Group();
    inner.position.set(...c3(0, -AXLE_Y, 0));
    outer.add(inner);
    const m = this.models;
    const lift = cloneModel(m.robot_lift);
    const ext = cloneModel(m.robot_extractor);
    const fA = cloneModel(m.finger);
    const fB = cloneModel(m.finger);
    inner.add(cloneModel(m.robot_base), lift, ext, fA, fB);
    const light = new THREE.PointLight(COLORS.green, 0, 0.4);
    light.position.set(...c3(0, -40, 70));
    inner.add(light);
    this.root.add(outer);
    this.robot = {outer, inner, lift, ext, fA, fB, light};
  }

  /** Robot camera pose in three.js world coordinates (for the camera view). */
  robotCamera(cam: THREE.PerspectiveCamera) {
    const s = this.sim.robot;
    const lens = new THREE.Vector3(...c3(CAM_LENS.x, CAM_LENS.y, s.Z + CAM_LENS.dz));
    const ahead = new THREE.Vector3(...c3(CAM_LENS.x, CAM_LENS.y + 100, s.Z + CAM_LENS.dz));
    this.robot.inner.updateWorldMatrix(true, false);
    cam.position.copy(lens.applyMatrix4(this.robot.inner.matrixWorld));
    cam.lookAt(ahead.applyMatrix4(this.robot.inner.matrixWorld));
  }

  /** True when scene geometry sits between the robot camera and a world point (CAD mm). */
  occluded(cam: THREE.PerspectiveCamera, p: [number, number, number]) {
    const target = new THREE.Vector3(...c3(...p));
    const dir = target.clone().sub(cam.position);
    const dist = dir.length();
    this.ray.set(cam.position, dir.normalize());
    this.ray.camera = cam;
    this.ray.far = dist - 0.004;
    this.ray.near = 0.005;
    for (const h of this.ray.intersectObjects(this.root.children, true)) {
      let o: THREE.Object3D | null = h.object;
      let skip = false;
      while (o) {
        if (o.userData.noOcclude) skip = true;
        o = o.parent;
      }
      if (!skip && (h.object as THREE.Mesh).isMesh) return true;
    }
    return false;
  }
  private ray = new THREE.Raycaster();

  robotWorldPos() {
    return new THREE.Vector3(...c3(this.sim.robot.pose.x, this.sim.robot.pose.y, 120));
  }

  stationWorldPos(id: string) {
    const st = this.sim.world.station(id);
    return new THREE.Vector3(...c3(st.x, st.y, 200));
  }

  /** Place everything from the sim state. `time` = wall seconds, for blinking. */
  sync(time: number) {
    const sim = this.sim;
    const r = sim.robot;
    const R = this.robot;
    R.outer.position.set(...c3(r.pose.x, r.pose.y, 0));
    R.outer.rotation.y = r.pose.th;
    R.lift.position.set(...c3(0, 0, r.Z));
    R.ext.position.set(...c3(0, r.Y, r.Z));
    R.fA.position.set(...c3(FINGER_X, Y_NOTCH_HOME + r.Y, r.Z + FINGER_DZ.A));
    R.fA.rotation.z = (r.fA * Math.PI) / 2;
    R.fB.position.set(...c3(FINGER_X, Y_NOTCH_HOME + r.Y, r.Z + FINGER_DZ.B));
    R.fB.rotation.z = (r.fB * Math.PI) / 2;
    R.light.intensity = sim.battery.charging ? 0.3 + 0.15 * Math.sin(time * 5) : 0;

    // caddies
    const w = sim.world;
    for (const [id, l] of w.loc) {
      const o = this.caddyObj(id);
      if (l.at === 'gone') {
        o.parent?.remove(o);
        continue;
      }
      if (l.at === 'shelf') {
        const sv = this.stations.get(l.st)!;
        if (o.parent !== sv.group) sv.group.add(o);
        o.position.set(...c3(0, 0, sv.st.shelves[l.i]));
      } else {
        if (o.parent !== R.inner) R.inner.add(o);
        o.position.set(...c3(0, w.trayY.get(id) ?? -Y_PULL, r.Z + 1 + (l.slot === 'A' ? BAY_PITCH : 0)));
      }
      const st = sim.health.get(id).status;
      setEmissive(o, st === 'FAILED' ? 0.55 + 0.35 * Math.sin(time * 6) : st === 'WARN' ? 0.12 : 0);
    }

    // station LEDs, lamps, labels
    const blink = Math.floor(time * 4) % 2 === 0;
    for (const sv of this.stations.values()) {
      sv.st.shelves.forEach((_, i) => {
        const id = w.at(sv.st.id, i);
        const led = sv.leds[i];
        const mat = led.material as THREE.MeshStandardMaterial;
        let col: string = COLORS.green;
        let k = 2;
        if (id === null) {
          col = COLORS.amber;
          k = sv.st.kind === 'rack' ? 1.2 : 0.05;
        } else {
          const st = sim.health.get(id).status;
          if (st === 'FAILED') {
            col = COLORS.red;
            k = blink ? 4 : 0.5;
          } else if (st === 'WARN') col = COLORS.amber;
          else if (sv.st.kind === 'rack' && sim.raid.get(sv.st.id)?.state === 'REBUILDING' && sim.jobs.some((j) => j.fresh === id)) {
            col = COLORS.blue;
            k = 1.5 + Math.sin(time * 8);
          }
        }
        mat.color.set(col);
        mat.emissive.set(col);
        mat.emissiveIntensity = k;
      });
      if (sv.st.kind === 'rack') {
        const raid = sim.raid.get(sv.st.id)!;
        const serving = sim.mission.job?.rack === sv.st.id;
        const lamp = (serving && (sim.paused || sim.mission.fault)) ? 2 : raid.state !== 'OPTIMAL' || serving ? 1 : 0;
        sv.lamps.forEach((m, i) => {
          (m.material as THREE.MeshStandardMaterial).emissiveIntensity = i === lamp ? (i === 2 ? (blink ? 6 : 2.5) : 5) : 0.08;
        });
        const col = raid.state === 'OPTIMAL' ? COLORS.green : raid.state === 'REBUILDING' ? COLORS.blue : raid.state === 'DEGRADED' ? COLORS.amber : COLORS.red;
        const sub = raid.state === 'REBUILDING' ? `REBUILD ${(raid.progress * 100).toFixed(0)} %` : `RAID ${raid.state}`;
        sv.label.set(sv.st.label, sub, col);
      } else {
        const s1 = w.at('home', 0) !== null;
        const s2 = w.at('home', 1) !== null;
        sv.label.set('Home · spare station', `S1 ${s1 ? 'spare ✓' : 'empty'} · S2 ${s2 ? 'RMA' : 'free'}`, s1 && !s2 ? COLORS.green : COLORS.amber);
      }
    }

    // route ahead of the robot
    const pts = sim.mission.route;
    const key = pts.map((p) => p.join(',')).join(';');
    if (pts.length < 2) {
      this.route.visible = false;
      this.target.visible = false;
    } else {
      if (key !== this.routeKey) {
        this.routeKey = key;
        this.route.geometry.setFromPoints(pts.map(([x, y]) => new THREE.Vector3(...c3(x, y, 3))));
        this.route.computeLineDistances();
        const e = pts[pts.length - 1];
        this.target.position.set(...c3(e[0], e[1], 3));
      }
      this.route.visible = true;
      this.target.visible = true;
      (this.route.material as THREE.LineDashedMaterial).opacity = 0.6 + 0.3 * Math.sin(time * 4);
    }
  }
}

