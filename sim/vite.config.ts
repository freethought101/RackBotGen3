import {defineConfig} from 'vite';
import {viteSingleFile} from 'vite-plugin-singlefile';

// One self-contained dist/index.html (scripts, styles and the CAD meshes inlined) that opens from disk, offline.
export default defineConfig({
  plugins: [viteSingleFile()],
  server: {fs: {allow: ['..']}},
  build: {assetsInlineLimit: 100_000_000, chunkSizeWarningLimit: 20_000},
});
