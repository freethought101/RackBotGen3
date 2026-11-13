// Render several stills of a composition with one bundle: node stills.mjs <composition> <outDir> <scale> <frame>...
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';

const [id, outDir, scale, ...frames] = process.argv.slice(2);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id, chromiumOptions: {gl: 'angle'}});
for (const f of frames.map(Number)) {
  const output = path.join(outDir, `${id}-${String(f).padStart(4, '0')}.jpg`);
  await renderStill({serveUrl, composition, frame: f, output, imageFormat: 'jpeg', scale: Number(scale), chromiumOptions: {gl: 'angle'}});
  console.log(output);
}
