import {ThreeCanvas} from '@remotion/three';
import {AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {H, TOTAL, W} from './constants';
import {Close, Delta, Hook, How, Problem, Reveal, Swap} from './overlays/scenes';
import {Vignette} from './overlays/ui';
import {World} from './three/World';

export const Film: React.FC = () => {
  const f = useCurrentFrame();
  const fadeIn = interpolate(f, [0, 24], [1, 0], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D10'}}>
      <ThreeCanvas width={W} height={H} shadows gl={{antialias: true, preserveDrawingBuffer: true}} camera={{fov: 30, near: 0.02, far: 30}}>
        <World />
      </ThreeCanvas>
      <Vignette />
      <Hook />
      <Problem />
      <Reveal />
      <How />
      <Swap />
      <Delta />
      <Close />
      <AbsoluteFill style={{background: '#000', opacity: fadeIn}} />
      <Audio src={staticFile('audio/bed.wav')} volume={(fr) => interpolate(fr, [0, 20, TOTAL - 40, TOTAL], [0, 1, 1, 0], {extrapolateRight: 'clamp'})} />
    </AbsoluteFill>
  );
};
