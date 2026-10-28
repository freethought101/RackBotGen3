import {Grid, Line, useGLTF} from '@react-three/drei';
import {useThree} from '@react-three/fiber';
import {useLayoutEffect, useMemo} from 'react';
import {staticFile, useCurrentFrame} from 'remotion';
import * as THREE from 'three';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';
import {BayState, CaddyMode, ROUTES, smooth, stateAt, WorldState} from '../anim';
import {cameraAt} from '../camera';
import {AXLE_Y, BAY_PITCH, CAM_LENS, COLORS, FINGER_DZ, FINGER_X, H_BAY, H_SPARE, SCENES, SPARE_D, SPARE_X, TAG_APPROACH, TOWER, Y_NOTCH_HOME, Y_PULL} from '../constants';
import {c3, clamp01} from '../geom';
import {tagTexture} from './tag';

const MODELS = ['robot_base', 'robot_lift', 'robot_extractor', 'finger', 'caddy', 'rack', 'spare'] as const;
MODELS.forEach((m) => useGLTF.preload(staticFile(`models/${m}.glb`)));

function useModel(name: (typeof MODELS)[number], tint?: THREE.ColorRepresentation) {
  const {scene} = useGLTF(staticFile(`models/${name}.glb`));
  return useMemo(() => {
    const s = scene.clone(true);
    s.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      m.castShadow = true;
      m.receiveShadow = true;
      const mats = (Array.isArray(m.material) ? m.material : [m.material]).map((mat) => {
        const c = (mat as THREE.MeshStandardMaterial).clone();
        c.envMapIntensity = 0.9;
        if (tint) {
          c.emissive = new THREE.Color(tint);
          c.emissiveIntensity = 0;
        }
        return c;
      });
      m.material = Array.isArray(m.material) ? mats : mats[0];
    });
    return s;
  }, [scene, tint]);
}

function setEmissive(obj: THREE.Object3D, k: number) {
  obj.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh) return;
    for (const mat of Array.isArray(m.material) ? m.material : [m.material]) (mat as THREE.MeshStandardMaterial).emissiveIntensity = k;
  });
}

const Prim: React.FC<{object: THREE.Object3D; position?: [number, number, number]; rotation?: [number, number, number]}> = ({object, ...p}) => (
  <primitive object={object} {...p} />
);

// ---- camera + environment ------------------------------------------------------------------
const CameraRig: React.FC<{frame: number; envK: number}> = ({frame, envK}) => {
  const {camera, gl, scene} = useThree();
  const cam = cameraAt(frame);
  const pc = camera as THREE.PerspectiveCamera;
  pc.position.set(...c3(...cam.pos));
  pc.fov = cam.fov;
  pc.near = 0.02;
  pc.far = 30;
  pc.lookAt(new THREE.Vector3(...c3(...cam.target)));
  pc.updateProjectionMatrix();
  scene.environmentIntensity = envK;
  useLayoutEffect(() => {
    const pm = new THREE.PMREMGenerator(gl);
    const env = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = env;
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
    return () => env.dispose();
  }, [gl, scene]);
  return null;
};

// ---- small emissive bits ---------------------------------------------------------------------
const Glow: React.FC<{pos: [number, number, number]; size: [number, number, number]; color: string; k: number}> = ({pos, size, color, k}) => (
  <mesh position={pos}>
    <boxGeometry args={size} />
    <meshStandardMaterial color={color} emissive={color} emissiveIntensity={k} toneMapped={false} />
  </mesh>
);

const LED_COLOR: Record<BayState, string> = {ok: COLORS.green, new: COLORS.green, failed: COLORS.red, empty: COLORS.amber};

const BayLeds: React.FC<{s: WorldState; frame: number; heights: number[]; states?: BayState[]}> = ({s, frame, heights, states}) => (
  <>
    {heights.map((h, i) => {
      const st = states ? states[i] : 'ok';
      const blink = st === 'failed' ? (Math.floor(frame / 8) % 2 === 0 ? 4 : 0.6) : st === 'new' ? 2 + 1.5 * Math.sin(frame / 4) : 2;
      return <Glow key={i} pos={c3(-62, -4, h + 34)} size={[0.006, 0.006, 0.003]} color={LED_COLOR[st]} k={blink} />;
    })}
  </>
);

const TowerLight: React.FC<{s: WorldState; frame: number}> = ({s, frame}) => {
  const seg = (TOWER.z1 - TOWER.z0) / 3;
  const order = [['green', COLORS.green], ['amber', COLORS.amber], ['red', COLORS.red]] as const;
  return (
    <>
      {order.map(([name, col], i) => {
        const on = s.light === name;
        const k = on ? (name === 'red' ? (Math.floor(frame / 10) % 2 ? 6 : 2.5) : 5) : 0.08;
        const [x, y, z] = c3(TOWER.x, TOWER.y, TOWER.z0 + seg * (i + 0.5));
        return (
          <group key={name}>
            <mesh position={[x, y, z]}>
              <cylinderGeometry args={[(TOWER.r + 0.8) / 1000, (TOWER.r + 0.8) / 1000, (seg - 3) / 1000, 32]} />
              <meshStandardMaterial color={col} emissive={col} emissiveIntensity={k} transparent opacity={0.92} toneMapped={false} />
            </mesh>
            {on && <pointLight position={[x, y, z]} color={col} intensity={0.25} distance={0.6} />}
          </group>
        );
      })}
    </>
  );
};

const Tag: React.FC<{id: number; at: [number, number, number]; size: number}> = ({id, at, size}) => {
  const tex = useMemo(() => tagTexture(id), [id]);
  return (
    <mesh position={c3(...at)}>
      <planeGeometry args={[size / 1000, size / 1000]} />
      <meshBasicMaterial map={tex} toneMapped={false} />
    </mesh>
  );
};

// ---- caddies -----------------------------------------------------------------------------------
const Caddy: React.FC<{obj: THREE.Object3D; m: CaddyMode; s: WorldState; where: 'rack' | 'spare' | 'robot'}> = ({obj, m, s, where}) => {
  if (m.mode !== where) return null;
  if (m.mode === 'rack') return <Prim object={obj} position={c3(0, 0, H_BAY[m.bay])} />;
  if (m.mode === 'spare') return <Prim object={obj} position={c3(0, 0, H_SPARE[m.slot])} />;
  const engaged = (m.slot === 'A' ? s.fA : s.fB) > 0.5;
  const y = (engaged ? s.Y : 0) - Y_PULL;
  return <Prim object={obj} position={c3(0, y, s.Z + 1 + (m.slot === 'A' ? BAY_PITCH : 0))} />;
};

// IMX708 wide (Camera Module 3 Wide): ~102° x 67° field of view, drawn as a wire frustum looking toward the rack.
const Frustum: React.FC<{lens: [number, number, number]; k: number}> = ({lens, k}) => {
  const d = 0.26;
  const hw = d * Math.tan((51 * Math.PI) / 180);
  const hh = d * Math.tan((33.5 * Math.PI) / 180);
  const [x, y, z] = lens;
  const corners: [number, number, number][] = [[x - hw, y - hh, z - d], [x + hw, y - hh, z - d], [x + hw, y + hh, z - d], [x - hw, y + hh, z - d]];
  const shape = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const p = [lens, corners[0], corners[1], lens, corners[1], corners[2], lens, corners[2], corners[3], lens, corners[3], corners[0]].flat();
    g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
    return g;
  }, [x, y, z]);
  return (
    <>
      <mesh geometry={shape}>
        <meshBasicMaterial color={COLORS.blue} transparent opacity={0.1 * k} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {corners.map((c, i) => <Line key={i} points={[lens, c]} color={COLORS.blue} lineWidth={1.5} transparent opacity={0.9 * k} />)}
      <Line points={[...corners, corners[0]]} color={COLORS.blue} lineWidth={1.5} transparent opacity={0.9 * k} />
    </>
  );
};

// ---- robot -----------------------------------------------------------------------------------
const Robot: React.FC<{s: WorldState; frame: number; caddies: React.ReactNode; showFrustum: number}> = ({s, frame, caddies, showFrustum}) => {
  const base = useModel('robot_base');
  const lift = useModel('robot_lift');
  const ext = useModel('robot_extractor');
  const fA = useModel('finger');
  const fB = useModel('finger');
  const fingers: [THREE.Object3D, number, number][] = [[fA, s.fA, FINGER_DZ.A], [fB, s.fB, FINGER_DZ.B]];
  const lens = c3(CAM_LENS.x, CAM_LENS.y, s.Z + CAM_LENS.dz);
  return (
    <group position={c3(s.cx, s.cy, 0)} rotation={[0, s.th, 0]}>
      <group position={c3(0, -AXLE_Y, 0)}>
        <Prim object={base} />
        <Prim object={lift} position={c3(0, 0, s.Z)} />
        <Prim object={ext} position={c3(0, s.Y, s.Z)} />
        {fingers.map(([o, f, dz], i) => (
          <Prim key={i} object={o} position={c3(FINGER_X, Y_NOTCH_HOME + s.Y, s.Z + dz)} rotation={[0, 0, (f * Math.PI) / 2]} />
        ))}
        {caddies}
        {showFrustum > 0 && (
          // IMX708 wide: ~102° horizontal; a 4-sided cone opening toward +y (rack side)
          <Frustum lens={lens} k={showFrustum} />
        )}
        {s.charging && <pointLight position={c3(0, -40, 70)} color={COLORS.green} intensity={0.35 + 0.15 * Math.sin(frame / 6)} distance={0.4} />}
      </group>
    </group>
  );
};

// ---- planned route: the path still ahead of the robot, drawn on the floor like a nav overlay ------------
const RouteLine: React.FC<{frame: number}> = ({frame}) => {
  const r = ROUTES.find((q) => frame >= q.f0 - 40 && frame <= q.f1 + 12);
  if (!r) return null;
  const k = clamp01(Math.min((frame - (r.f0 - 40)) / 12, (r.f1 + 12 - frame) / 12));
  const i = Math.floor(smooth(clamp01((frame - r.f0) / (r.f1 - r.f0))) * (r.pts.length - 1));
  const pts = r.pts.slice(i).map(([x, y]) => c3(x, y, 2));
  if (pts.length < 2) return null;
  const end = pts[pts.length - 1];
  return (
    <>
      <Line points={pts} color={COLORS.accent} lineWidth={3} dashed dashSize={0.04} gapSize={0.025} transparent opacity={0.85 * k} />
      <mesh position={end} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.035, 0.05, 40]} />
        <meshBasicMaterial color={COLORS.accent} transparent opacity={0.9 * k} toneMapped={false} />
      </mesh>
    </>
  );
};

// ---- the data hall: a dark row of racks for the hook --------------------------------------------
const HALL_X = [-1350, -1000, -650, -330, 330, 650, 1000, 1350];
const Hall: React.FC<{frame: number}> = ({frame}) => {
  const racks = HALL_X.map(() => useModel('rack'));
  const caddies = HALL_X.map(() => H_BAY.map(() => useModel('caddy')));
  return (
    <>
      {HALL_X.map((x, i) => (
        <group key={x} position={c3(x, 0, 0)}>
          <Prim object={racks[i]} />
          {H_BAY.map((h, b) => (
            <group key={b}>
              <Prim object={caddies[i][b]} position={c3(0, 0, h)} />
              <Glow pos={c3(-62, -4, h + 34)} size={[0.006, 0.006, 0.003]} color={COLORS.green}
                k={(Math.floor(frame / (5 + ((i * 7 + b * 3) % 6))) + i + b) % 3 === 0 ? 0.6 : 2.4} />
            </group>
          ))}
        </group>
      ))}
    </>
  );
};

// ---- the world ---------------------------------------------------------------------------------
export const World: React.FC = () => {
  const frame = useCurrentFrame();
  const s = stateAt(frame);
  const rack = useModel('rack');
  const spare = useModel('spare');
  const goodCaddies = [useModel('caddy'), useModel('caddy'), useModel('caddy')];
  const failed = useModel('caddy', COLORS.red);
  const spareCaddy = useModel('caddy');

  const studio = frame >= SCENES.reveal[0] && frame < SCENES.how[1];
  const dark = frame < SCENES.reveal[0];
  const showRobot = frame >= SCENES.reveal[0];
  const arena = frame >= SCENES.swap[0]; // the wide rack-to-spare floor
  const failedGlow = s.bays[1] === 'failed' || (s.caddies.failed.mode !== 'rack' && frame < SCENES.delta[0]) ? 0.25 + 0.2 * Math.sin(frame / 5) : 0;
  setEmissive(failed, failedGlow);
  const how = frame - SCENES.how[0];
  const frustum = how > 400 && how < 500 ? clamp01(Math.min((how - 400) / 15, (500 - how) / 15)) : 0;

  // Light rig: dark data hall for the hook, studio for the reveal, warm work light for the demo.
  const key = dark ? 0.12 : 2.2;
  const amb = dark ? 0.05 : 0.35;

  const caddyRobot = (
    <>
      <Caddy obj={spareCaddy} m={s.caddies.spare} s={s} where="robot" />
      <Caddy obj={failed} m={s.caddies.failed} s={s} where="robot" />
    </>
  );

  return (
    <>
      <CameraRig frame={frame} envK={dark ? 0.06 : 1} />
      {dark && <Hall frame={frame} />}
      <color attach="background" args={[dark ? '#05070A' : COLORS.bg]} />
      <fog attach="fog" args={[dark ? '#05070A' : COLORS.bg, arena ? 4 : 1.6, arena ? 11 : 5.5]} />
      <hemisphereLight args={['#dfe8ff', '#1a1c20', amb]} />
      <directionalLight
        position={[1.2, 2.2, 1.6]}
        intensity={key}
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-3.4}
        shadow-camera-right={3.4}
        shadow-camera-top={3.4}
        shadow-camera-bottom={-3.4}
        shadow-bias={-0.0004}
      />
      <directionalLight position={[-1.5, 1.0, -1.2]} intensity={dark ? 0.35 : 1.2} color="#7fb2ff" />
      <directionalLight position={[-0.6, 0.8, 2.0]} intensity={dark ? 0.03 : 0.5} color="#ffe2c4" />
      {dark && <pointLight position={c3(-40, -120, H_BAY[1] + 30)} color={COLORS.red} intensity={0.02 + 0.02 * (Math.floor(frame / 8) % 2)} distance={0.4} />}

      {/* floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.0005, 0]} receiveShadow>
        <planeGeometry args={[30, 30]} />
        <meshStandardMaterial color={dark ? '#07090C' : '#121419'} roughness={0.9} />
      </mesh>
      <Grid
        position={[0, 0.0003, 0]}
        args={[12, 12]}
        cellSize={0.05}
        cellThickness={0.5}
        cellColor={dark ? '#10141a' : '#1d222a'}
        sectionSize={0.25}
        sectionThickness={1}
        sectionColor={dark ? '#18202a' : '#2a313b'}
        fadeDistance={arena ? 9 : 4}
        fadeStrength={1.2}
        infiniteGrid
      />

      {!studio && (
        <>
          <group>
            <Prim object={rack} />
            {[0, 2, 3].map((b, i) => <Prim key={b} object={goodCaddies[i]} position={c3(0, 0, H_BAY[b])} />)}
            <Caddy obj={failed} m={s.caddies.failed} s={s} where="rack" />
            <Caddy obj={spareCaddy} m={s.caddies.spare} s={s} where="rack" />
            <BayLeds s={s} frame={frame} heights={H_BAY} states={s.bays} />
            <TowerLight s={s} frame={frame} />
            <Tag id={0} at={[TAG_APPROACH.x, TAG_APPROACH.y - 0.2, TAG_APPROACH.z]} size={50} />
          </group>
          <group position={c3(SPARE_X, -SPARE_D, 0)} rotation={[0, Math.PI, 0]}>
            <Prim object={spare} />
            <Caddy obj={failed} m={s.caddies.failed} s={s} where="spare" />
            <Caddy obj={spareCaddy} m={s.caddies.spare} s={s} where="spare" />
            <Tag id={10} at={[TAG_APPROACH.x, TAG_APPROACH.y - 0.2, TAG_APPROACH.z]} size={50} />
          </group>
        </>
      )}
      {arena && <RouteLine frame={frame} />}
      {showRobot && <Robot s={s} frame={frame} caddies={caddyRobot} showFrustum={frustum} />}
    </>
  );
};
