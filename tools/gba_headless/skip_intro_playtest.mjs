import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
import path from 'node:path';

const romPath = process.argv[2];
const outputDir = process.argv[3] ?? 'playtest_output/skip';
const cycles = Number(process.argv[4] ?? 80);
if (!romPath) {
  console.error('Usage: node skip_intro_playtest.mjs ROM OUTPUT_DIR [CYCLES]');
  process.exit(2);
}
await fs.mkdir(outputDir, { recursive: true });
const result = { romPath, outputDir, cycles, status: 'unknown', error: null, screenshots: [] };
try {
  const runtime = await HeadlessRuntime.create({ romPath, outputDir, logFn: () => {} });
  let script = `await wait({ frames: 30 });\nawait takeScreenshot({ name: 't000_start' });\n`;
  for (let i = 0; i < cycles; i++) {
    const btn = i % 4 === 0 ? 'start' : (i % 4 === 1 ? 'a' : (i % 4 === 2 ? 'b' : 'start'));
    script += `await press('${btn}', { hold: 6 });\nawait wait({ frames: 24 });\n`;
    if (i % 10 === 9) script += `await takeScreenshot({ name: 't${String(i + 1).padStart(3, '0')}' });\n`;
  }
  script += `await takeScreenshot({ name: 'final' });\nawait takeMemorySnapshot({ name: 'io-final', region: 'io' });\n`;
  await runtime.executeScript(script);
  result.status = 'PASS_RUNTIME_SCRIPT_COMPLETED';
  result.screenshots = runtime.host.generatedFiles.filter((f) => f.startsWith('screenshot'));
  await runtime.writeFinalSaveState();
} catch (err) {
  result.status = 'FAIL_RUNTIME_EXCEPTION';
  result.error = String(err && err.stack ? err.stack : err);
}
await fs.writeFile(path.join(outputDir, 'skip-playtest-result.json'), JSON.stringify(result, null, 2));
if (result.status.startsWith('FAIL')) {
  console.error(result.error);
  process.exit(1);
}
console.log(result.status);
