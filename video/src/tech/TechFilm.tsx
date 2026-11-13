// CORVIN technical film: 150 s, no voice-over. The 3D world, the scene overlays and the audio layer.
import {ThreeCanvas} from '@remotion/three';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {H, W} from '../constants';
import {Anatomy, Close, Drive, Extract, Intro, Lift, Make, Power, Safety, Swap, System, Vision} from './scenes';
import {SfxLayer} from './sfx';
import {BLUE} from './theme';
import {T_TOTAL} from './timeline';
import {TechWorld} from './World';

export const TechFilm: React.FC = () => {
  const f = useCurrentFrame();
  const fadeIn = interpolate(f, [0, 20], [1, 0], {extrapolateRight: 'clamp'});
  const fadeOut = interpolate(f, [T_TOTAL - 24, T_TOTAL], [0, 1], {extrapolateLeft: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: BLUE.bg}}>
      <ThreeCanvas width={W} height={H} shadows gl={{antialias: true, preserveDrawingBuffer: true}} camera={{fov: 30, near: 0.02, far: 40}}>
        <TechWorld />
      </ThreeCanvas>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(3,10,18,0) 50%, rgba(3,10,18,0.6) 100%)'}} />
      <Intro />
      <System />
      <Anatomy />
      <Drive />
      <Lift />
      <Extract />
      <Vision />
      <Power />
      <Safety />
      <Swap />
      <Make />
      <Close />
      <AbsoluteFill style={{background: '#02070d', opacity: Math.max(fadeIn, fadeOut)}} />
      <SfxLayer />
    </AbsoluteFill>
  );
};
