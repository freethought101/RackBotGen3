// 3D scene of the technical film: per-subsystem CAD groups (export/export_tech_glb.py) restyled for the blue
// look, with exploded view, ghosting of the parts not being explained, real wheel rotation, the studio plinth and
// the rack / base-station floor.
import {Grid, Line, useGLTF} from '@react-three/drei';
import {useThree} from '@react-three/fiber';
import {useLayoutEffect, useMemo} from 'react';
import {staticFile, useCurrentFrame} from 'remotion';
import * as THREE from 'three';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';
import {AXLE_Y, BAY_PITCH, CAM_LENS, FINGER_DZ, FINGER_X, H_BAY, H_SPARE, SPARE_D, SPARE_X, TAG_APPROACH, Y_NOTCH_HOME, Y_PULL} from '../constants';
import {smooth} from '../engine';
import {c3, clamp01, V3} from '../geom';
import {tagTexture} from '../three/tag';
import {techCameraAt} from './camera';
import {BLUE} from './theme';
import {BayState, CaddyMode, EXPLODE, explodeAt, focusAt, inStudio, ROUTES, sceneAt, stateAt, TechState, TS} from './timeline';

const BASE = ['chassis', 'nose', 'wheel_left', 'wheel_right', 'drive_motor_left', 'drive_motor_right', 'mast', 'zdrive', 'electronics', 'power'] as const;
const LIFT = ['zcarriage', 'tray', 'camera', 'yrail'] as const;
const EXT = ['ycarriage', 'servo_a', 'servo_b'] as const;
const STATION = ['rack', 'rack_electronics', 'rack_lamps', 'spare'] as const;
const TECH = [...BASE, ...LIFT, ...EXT, ...STATION];
TECH.forEach((m) => useGLTF.preload(staticFile(`models/tech/${m}.glb`)));
useGLTF.preload(staticFile('models/caddy.glb'));
useGLTF.preload(staticFile('models/finger.glb'));

// ---- materials ---------------------------------------------------------------------------------------
const near = (c: THREE.Color, r: number, g: number, b: number, tol = 0.04) =>
  Math.abs(c.r - r) < tol && Math.abs(c.g - g) < tol && Math.abs(c.b - b) < tol;

/** Restyle a CAD material for the blue film: CAD orange accents -> blue, warm printed white -> cool white,
 * aluminium extrusions metallic. Colours compare in linear space (as stored in the GLB). */
function restyle(src: THREE.MeshStandardMaterial, role: 'robot' | 'caddy' | 'station'): THREE.MeshStandardMaterial {
  const m = src.clone();
  const c = m.color;
  m.envMapIntensity = 1.0;
  m.roughness = 0.55;
  m.metalness = 0.05;
  if (near(c, 0.745, 0.195, 0.014)) {
    m.color.set(role === 'caddy' ? BLUE.caddy : BLUE.robotAccent);
    m.roughness = 0.42;
  } else if (near(c, 0.807, 0.776, 0.701)) {
    m.color.set(BLUE.printed);
    m.roughness = 0.5;
  } else if (near(c, 0.386, 0.429, 0.479)) {
    m.color.set('#B9C3CF');
    m.metalness = 0.85;
    m.roughness = 0.3;
  } else if (near(c, 0.262, 0.292, 0.328)) {
    m.color.set('#5D6876');
    m.metalness = 0.7;
    m.roughness = 0.36;
  } else if (near(c, 0.888, 0.888, 0.888)) {
    m.color.set('#D7DEE7');
  }
  m.emissive = new THREE.Color(BLUE.cyan);
  m.emissiveIntensity = 0;
  m.userData.baseOpacity = 1;
  return m;
}

function useModel(path: string, role: 'robot' | 'caddy' | 'station' = 'robot') {
  const {scene} = useGLTF(staticFile(path));
  return useMemo(() => {
    const s = scene.clone(true);
    s.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      const mats = (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).map((x) => restyle(x as THREE.MeshStandardMaterial, role));
      mesh.material = Array.isArray(mesh.material) ? mats : mats[0];
    });
    return s;
  }, [scene, role]);
}

/** ghost 0..1 fades the part to a faint x-ray; glow 0..1 lights it in the accent colour. */
function setLook(obj: THREE.Object3D, ghost: number, glow: number, glowColor: string = BLUE.cyan) {
  obj.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    mesh.castShadow = ghost < 0.5;
    for (const mat of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      const m = mat as THREE.MeshStandardMaterial;
      const op = 1 - 0.86 * ghost;
      m.transparent = op < 0.999;
      m.opacity = op;
      m.depthWrite = op > 0.6;
      m.emissive.set(glowColor);
      m.emissiveIntensity = glow;
    }
  });
}

const Prim: React.FC<{object: THREE.Object3D; position?: V3; rotation?: V3}> = ({object, ...p}) => <primitive object={object} {...p} />;

// ---- camera + environment ---------------------------------------------------------------------------
const Rig: React.FC<{frame: number}> = ({frame}) => {
  const {camera, gl, scene} = useThree();
  const cam = techCameraAt(frame);
  const pc = camera as THREE.PerspectiveCamera;
  pc.position.set(...c3(...cam.pos));
  pc.fov = cam.fov;
  pc.near = 0.02;
  pc.far = 40;
  pc.lookAt(new THREE.Vector3(...c3(...cam.target)));
  pc.updateProjectionMatrix();
  useLayoutEffect(() => {
    const pm = new THREE.PMREMGenerator(gl);
    const env = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = env;
    scene.environmentIntensity = 0.75;
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.05;
    return () => env.dispose();
  }, [gl, scene]);
  return null;
};

const Tag: React.FC<{id: number; at: V3; size: number}> = ({id, at, size}) => {
  const tex = useMemo(() => tagTexture(id), [id]);
  return (
    <mesh position={c3(...at)}>
      <planeGeometry args={[size / 1000, size / 1000]} />
      <meshBasicMaterial map={tex} toneMapped={false} />
    </mesh>
  );
};

const Glow: React.FC<{pos: V3; size: V3; color: string; k: number}> = ({pos, size, color, k}) => (
  <mesh position={pos}>
    <boxGeometry args={size} />
    <meshStandardMaterial color={color} emissive={color} emissiveIntensity={k} toneMapped={false} />
  </mesh>
);

const LED: Record<BayState, string> = {ok: BLUE.ok, new: BLUE.ok, failed: BLUE.fault, empty: BLUE.amber};

// ---- caddies (one copy per place, so no object is ever handed between parents) ---------------------------
type Where = 'rack' | 'spare' | 'robot';
const Caddy: React.FC<{obj: THREE.Object3D; m: CaddyMode; s: TechState; where: Where; trayOff?: V3}> = ({obj, m, s, where, trayOff = [0, 0, 0]}) => {
  if (m.mode !== where) return null;
  if (m.mode === 'rack') return <Prim object={obj} position={c3(0, 0, H_BAY[m.bay])} />;
  if (m.mode === 'spare') return <Prim object={obj} position={c3(0, 0, H_SPARE[m.slot])} />;
  const engaged = (m.slot === 'A' ? s.fA : s.fB) > 0.5;
  const y = (engaged ? s.Y : 0) - Y_PULL;
  return <Prim object={obj} position={c3(trayOff[0], y + trayOff[1], s.Z + 1 + (m.slot === 'A' ? BAY_PITCH : 0) + trayOff[2])} />;
};

// ---- camera frustum (IMX708 wide, ~102° x 67°) -----------------------------------------------------
const Frustum: React.FC<{lens: V3; k: number}> = ({lens, k}) => {
  const d = 0.34;
  const hw = d * Math.tan((51 * Math.PI) / 180);
  const hh = d * Math.tan((33.5 * Math.PI) / 180);
  const [x, y, z] = lens;
  const corners: V3[] = [[x - hw, y - hh, z - d], [x + hw, y - hh, z - d], [x + hw, y + hh, z - d], [x - hw, y + hh, z - d]];
  const shape = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const p = [lens, corners[0], corners[1], lens, corners[1], corners[2], lens, corners[2], corners[3], lens, corners[3], corners[0]].flat();
    g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
    return g;
  }, [x, y, z]);
  return (
    <>
      <mesh geometry={shape}>
        <meshBasicMaterial color={BLUE.cyan} transparent opacity={0.08 * k} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {corners.map((c, i) => <Line key={i} points={[lens, c]} color={BLUE.cyan} lineWidth={1.5} transparent opacity={0.85 * k} />)}
      <Line points={[...corners, corners[0]]} color={BLUE.cyan} lineWidth={1.5} transparent opacity={0.85 * k} />
    </>
  );
};

// ---- robot ------------------------------------------------------------------------------------------
const WHEEL_PIVOT = c3(0, AXLE_Y, 40);

const Robot: React.FC<{s: TechState; frame: number; caddies: (off: V3) => React.ReactNode}> = ({s, frame, caddies}) => {
  const parts = Object.fromEntries([...BASE, ...LIFT, ...EXT].map((n) => [n, useModel(`models/tech/${n}.glb`)])) as Record<string, THREE.Object3D>;
  const fA = useModel('models/finger.glb');
  const fB = useModel('models/finger.glb');
  const e = explodeAt(frame);
  const off = (n: string): V3 => {
    const o = EXPLODE[n] ?? [0, 0, 0];
    return [o[0] * e, o[1] * e, o[2] * e];
  };
  // focus: ghost everything outside the scene's groups, light the focused groups
  const {groups, k} = focusAt(frame);
  const pulse = 0.5 + 0.5 * Math.sin(frame / 9);
  const look = (n: string) => (groups.includes(n) ? [0, k * (0.14 + 0.1 * pulse)] : [k, 0]);
  for (const n of Object.keys(parts)) {
    const [g, gl] = look(n);
    setLook(parts[n], g, gl);
  }
  for (const f of [fA, fB]) {
    const [g, gl] = look('finger');
    setLook(f, g, gl);
  }
  const lens = c3(CAM_LENS.x + off('camera')[0], CAM_LENS.y + off('camera')[1], s.Z + CAM_LENS.dz + off('camera')[2]);
  const vision = sceneAt(frame) === 'vision' ? clamp01(Math.min((frame - TS.vision[0] - 20) / 20, (TS.vision[1] - 10 - frame) / 14)) : 0;
  const P = (n: string, z = 0, y = 0) => {
    const o = off(n);
    return <Prim key={n} object={parts[n]} position={c3(o[0], o[1] + y, o[2] + z)} />;
  };
  const wheel = (n: 'wheel_left' | 'wheel_right', ang: number) => {
    const o = off(n);
    const p = c3(o[0], o[1], o[2]);
    return (
      <group key={n} position={[WHEEL_PIVOT[0] + p[0], WHEEL_PIVOT[1] + p[1], WHEEL_PIVOT[2] + p[2]]}>
        <group rotation={[-ang, 0, 0]}>
          <Prim object={parts[n]} position={[-WHEEL_PIVOT[0], -WHEEL_PIVOT[1], -WHEEL_PIVOT[2]]} />
        </group>
      </group>
    );
  };
  return (
    <group position={c3(s.cx, s.cy, 0)} rotation={[0, s.th, 0]}>
      <group position={c3(0, -AXLE_Y, 0)}>
        {BASE.filter((n) => !n.startsWith('wheel')).map((n) => P(n))}
        {wheel('wheel_left', s.wheelL)}
        {wheel('wheel_right', s.wheelR)}
        {LIFT.map((n) => P(n, s.Z))}
        {EXT.map((n) => P(n, s.Z, s.Y))}
        {([[fA, s.fA, FINGER_DZ.A], [fB, s.fB, FINGER_DZ.B]] as [THREE.Object3D, number, number][]).map(([o, fv, dz], i) => {
          const q = off('finger');
          return <Prim key={i} object={o} position={c3(FINGER_X + q[0], Y_NOTCH_HOME + s.Y + q[1], s.Z + dz + q[2])} rotation={[0, 0, (fv * Math.PI) / 2]} />;
        })}
        {caddies(off('tray'))}
        {vision > 0 && <Frustum lens={lens} k={vision} />}
        {s.charging && <pointLight position={c3(0, -40, 70)} color={BLUE.ok} intensity={0.4 + 0.15 * Math.sin(frame / 6)} distance={0.45} />}
      </group>
    </group>
  );
};

// ---- planned route on the floor ------------------------------------------------------------------------
const RouteLine: React.FC<{frame: number}> = ({frame}) => {
  const r = ROUTES.find((q) => frame >= q.f0 - 40 && frame <= q.f1 + 12);
  if (!r) return null;
  const k = clamp01(Math.min((frame - (r.f0 - 40)) / 12, (r.f1 + 12 - frame) / 12));
  const i = Math.floor(smooth(clamp01((frame - r.f0) / (r.f1 - r.f0))) * (r.pts.length - 1));
  const pts = r.pts.slice(i).map(([x, y]) => c3(x, y, 2));
  if (pts.length < 2) return null;
  return (
    <>
      <Line points={pts} color={BLUE.cyan} lineWidth={3} dashed dashSize={0.04} gapSize={0.025} transparent opacity={0.9 * k} />
      <mesh position={pts[pts.length - 1]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.035, 0.05, 40]} />
        <meshBasicMaterial color={BLUE.cyan} transparent opacity={0.9 * k} toneMapped={false} />
      </mesh>
    </>
  );
};

// ---- studio plinth: a dark disc with a thin lit rim ---------------------------------------------------------
const Plinth: React.FC<{frame: number}> = ({frame}) => (
  <group position={[0, 0, 0]}>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.0006, 0]} receiveShadow>
      <circleGeometry args={[0.46, 96]} />
      <meshStandardMaterial color="#0c2133" roughness={0.35} metalness={0.4} />
    </mesh>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.0012, 0]}>
      <ringGeometry args={[0.455, 0.462, 128]} />
      <meshBasicMaterial color={BLUE.cyan} transparent opacity={0.55 + 0.1 * Math.sin(frame / 20)} toneMapped={false} />
    </mesh>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.0011, 0]}>
      <ringGeometry args={[0.462, 0.62, 128]} />
      <meshBasicMaterial color={BLUE.cyan} transparent opacity={0.05} toneMapped={false} />
    </mesh>
  </group>
);

// ---- the world ---------------------------------------------------------------------------------------
export const TechWorld: React.FC = () => {
  const frame = useCurrentFrame();
  const s = stateAt(frame);
  const scene = sceneAt(frame);
  const studio = inStudio(frame);

  const rack = useModel('models/tech/rack.glb', 'station');
  const rackEl = useModel('models/tech/rack_electronics.glb', 'station');
  const lamps = useModel('models/tech/rack_lamps.glb', 'station');
  const spare = useModel('models/tech/spare.glb', 'station');
  const good = [useModel('models/caddy.glb', 'caddy'), useModel('models/caddy.glb', 'caddy'), useModel('models/caddy.glb', 'caddy')];
  const failed = {rack: useModel('models/caddy.glb', 'caddy'), robot: useModel('models/caddy.glb', 'caddy'), spare: useModel('models/caddy.glb', 'caddy')};
  const spareC = {rack: useModel('models/caddy.glb', 'caddy'), robot: useModel('models/caddy.glb', 'caddy'), spare: useModel('models/caddy.glb', 'caddy')};

  // the failed drive breathes in the fault colour while it is the problem; caddies ghost with the robot's focus
  const {groups, k} = focusAt(frame);
  const caddyGhost = groups.length && !groups.includes('caddy') ? k : 0;
  const fault = s.bays[1] === 'failed' || (s.caddies.failed.mode !== 'rack' && scene === 'swap') ? 0.35 + 0.3 * Math.sin(frame / 5) : 0;
  Object.values(failed).forEach((o) => setLook(o, caddyGhost, fault, BLUE.fault));
  Object.values(spareC).forEach((o) => setLook(o, caddyGhost, 0));
  // rack lamps: light the one matching the controller state (red blinks)
  lamps.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    const m = mesh.material as THREE.MeshStandardMaterial;
    const c = m.color;
    const name = c.g > c.r && c.g > c.b ? 'green' : c.r > 0.5 && c.g > 0.3 ? 'amber' : 'red';
    const on = s.light === name;
    m.emissive.copy(c);
    m.emissiveIntensity = on ? (name === 'red' ? (Math.floor(frame / 8) % 2 ? 5 : 1.5) : 3.5) : 0.04;
    m.toneMapped = !on;
  });
  // safety scene: the rack electronics glow while they are explained
  const safetyK = scene === 'safety' ? clamp01(Math.min((frame - TS.safety[0] - 16) / 20, (TS.safety[1] - 8 - frame) / 14)) : 0;
  setLook(rackEl, 0, 0.12 * safetyK);

  const intro = scene === 'intro';
  const ik = intro ? clamp01((frame - 6) / 70) : 1;
  const sweep = intro ? -1.6 + 3.2 * clamp01(frame / 150) : 0.9;
  const lampLight = (() => {
    const [x, y, z] = c3(60, 145, 410);
    const col = s.light === 'green' ? BLUE.ok : s.light === 'amber' ? BLUE.amber : BLUE.fault;
    return <pointLight position={[x, y, z]} color={col} intensity={s.light === 'red' ? 0.5 : 0.25} distance={0.7} />;
  })();

  return (
    <>
      <Rig frame={frame} />
      <color attach="background" args={[BLUE.bg]} />
      <fog attach="fog" args={[BLUE.bg, studio ? 2.2 : 4.2, studio ? 7 : 12]} />
      <hemisphereLight args={['#bcd6ff', '#06101c', 0.45 * ik]} />
      <directionalLight
        position={[1.3, 2.4, 1.5]}
        intensity={2.1 * ik}
        color="#f2f7ff"
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-3.4}
        shadow-camera-right={3.4}
        shadow-camera-top={3.4}
        shadow-camera-bottom={-3.4}
        shadow-bias={-0.0004}
        shadow-radius={4}
      />
      {/* blue rim from behind; during the intro it sweeps across the robot */}
      <directionalLight position={[sweep, 1.1, -1.6]} intensity={intro ? 4.5 : 2.4} color={BLUE.cyan} />
      <directionalLight position={[-1.8, 0.7, 0.4]} intensity={0.9 * ik} color={BLUE.blue} />
      <directionalLight position={[0.2, 0.6, 2.2]} intensity={0.35 * ik} color="#dfe9ff" />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.0005, 0]} receiveShadow>
        <planeGeometry args={[40, 40]} />
        <meshStandardMaterial color="#0a1b2b" roughness={0.78} metalness={0.15} />
      </mesh>
      <Grid
        position={[0, 0.0003, 0]}
        args={[12, 12]}
        cellSize={0.05}
        cellThickness={0.5}
        cellColor="#12324a"
        sectionSize={0.25}
        sectionThickness={1}
        sectionColor="#1b4a6b"
        fadeDistance={studio ? 3.2 : 9}
        fadeStrength={1.4}
        infiniteGrid
      />
      {studio && <Plinth frame={frame} />}

      {!studio && (
        <>
          <group>
            <Prim object={rack} />
            <Prim object={rackEl} />
            <Prim object={lamps} />
            {lampLight}
            {[0, 2, 3].map((b, i) => <Prim key={b} object={good[i]} position={c3(0, 0, H_BAY[b])} />)}
            <Caddy obj={failed.rack} m={s.caddies.failed} s={s} where="rack" />
            <Caddy obj={spareC.rack} m={s.caddies.spare} s={s} where="rack" />
            {H_BAY.map((h, i) => {
              const st = s.bays[i];
              const kk = st === 'failed' ? (Math.floor(frame / 8) % 2 === 0 ? 4 : 0.6) : st === 'new' ? 2 + 1.5 * Math.sin(frame / 4) : 2;
              return <Glow key={i} pos={c3(-62, -4, h + 34)} size={[0.006, 0.006, 0.003]} color={LED[st]} k={kk} />;
            })}
            <Tag id={0} at={[TAG_APPROACH.x, TAG_APPROACH.y - 0.2, TAG_APPROACH.z]} size={50} />
          </group>
          <group position={c3(SPARE_X, -SPARE_D, 0)} rotation={[0, Math.PI, 0]}>
            <Prim object={spare} />
            <Caddy obj={failed.spare} m={s.caddies.failed} s={s} where="spare" />
            <Caddy obj={spareC.spare} m={s.caddies.spare} s={s} where="spare" />
            <Tag id={10} at={[TAG_APPROACH.x, TAG_APPROACH.y - 0.2, TAG_APPROACH.z]} size={50} />
          </group>
        </>
      )}
      {scene === 'swap' && <RouteLine frame={frame} />}
      <Robot
        s={s}
        frame={frame}
        caddies={(off) => (
          <>
            <Caddy obj={spareC.robot} m={s.caddies.spare} s={s} where="robot" trayOff={off} />
            <Caddy obj={failed.robot} m={s.caddies.failed} s={s} where="robot" trayOff={off} />
          </>
        )}
      />
    </>
  );
};
