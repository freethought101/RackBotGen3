import {Composition} from 'remotion';
import {Film} from './Film';
import {FPS, H, TOTAL, W} from './constants';
import {TechFilm} from './tech/TechFilm';
import {T_FPS, T_TOTAL} from './tech/timeline';

export const Root: React.FC = () => (
  <>
    <Composition id="RackBotPitch" component={Film} durationInFrames={TOTAL} fps={FPS} width={W} height={H} />
    <Composition id="CorvinTech" component={TechFilm} durationInFrames={T_TOTAL} fps={T_FPS} width={W} height={H} />
  </>
);
