// A deterministic AprilTag-style 8x8 marker (black border + 6x6 payload) as a canvas texture (copy of video/src/three/tag.ts).
import * as THREE from 'three';

export function tagTexture(id: number) {
  const n = 8;
  const px = 32;
  const c = document.createElement('canvas');
  c.width = c.height = (n + 2) * px;
  const g = c.getContext('2d')!;
  g.fillStyle = '#fff';
  g.fillRect(0, 0, c.width, c.height);
  g.fillStyle = '#000';
  g.fillRect(px, px, n * px, n * px);
  let seed = 2166136261 ^ (id * 16777619);
  const rnd = () => ((seed = Math.imul(seed ^ (seed >>> 15), 2246822507) >>> 0) & 0xffff) / 0xffff;
  g.fillStyle = '#fff';
  for (let i = 0; i < 6; i++) for (let j = 0; j < 6; j++) if (rnd() > 0.5) g.fillRect((i + 2) * px, (j + 2) * px, px, px);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
