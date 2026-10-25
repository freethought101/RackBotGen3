import {Composition} from 'remotion';
import {Film} from './Film';
import {FPS, H, TOTAL, W} from './constants';

export const Root: React.FC = () => (
  <Composition id="RackBotPitch" component={Film} durationInFrames={TOTAL} fps={FPS} width={W} height={H} />
);
