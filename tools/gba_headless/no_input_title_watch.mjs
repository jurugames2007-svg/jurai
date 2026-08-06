import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
const romPath = process.argv[2];
const outputDir = process.argv[3] ?? 'playtest_output/no_input_title';
const frames = Number(process.argv[4] ?? 720);
await fs.mkdir(outputDir, { recursive: true });
const runtime = await HeadlessRuntime.create({ romPath, outputDir, logFn: () => {} });
let script = '';
for (let f = 0; f <= frames; f += 60) {
  if (f > 0) script += `await wait({ frames: 60 });\n`;
  script += `await takeScreenshot({ name: 'f${String(f).padStart(4,'0')}' });\n`;
}
await runtime.executeScript(script);
await runtime.writeFinalSaveState();
console.log('done');
