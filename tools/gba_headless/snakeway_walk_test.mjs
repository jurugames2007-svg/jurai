import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
import path from 'node:path';

const romPath = process.argv[2];
const outputDir = process.argv[3] ?? 'playtest_output/snakeway_walk';
const savePath = process.argv[4] ?? null;
if (!romPath) {
  console.error('Usage: node snakeway_walk_test.mjs ROM OUTPUT_DIR [SAVE_STATE]');
  process.exit(2);
}
await fs.mkdir(outputDir, { recursive: true });
const result = { romPath, outputDir, savePath, status: 'unknown', error: null, screenshots: [] };
try {
  const options = { romPath, outputDir, logFn: () => {} };
  if (savePath) options.loadSavePath = savePath;
  const runtime = await HeadlessRuntime.create(options);
  const script = `
    await wait({ frames: 30 });
    await takeScreenshot({ name: 'walk_000_loaded' });
    await press('a', { hold: 8 });
    await wait({ frames: 60 });
    await takeScreenshot({ name: 'walk_010_after_a' });
    await press('start', { hold: 8 });
    await wait({ frames: 60 });
    await takeScreenshot({ name: 'walk_020_after_start' });
    await press('b', { hold: 8 });
    await wait({ frames: 40 });
    await takeScreenshot({ name: 'walk_030_after_b' });
    await press('right', { hold: 60 });
    await wait({ frames: 20 });
    await takeScreenshot({ name: 'walk_040_right_60' });
    await press('right', { hold: 120 });
    await wait({ frames: 20 });
    await takeScreenshot({ name: 'walk_050_right_180' });
    await press('right', { hold: 180 });
    await wait({ frames: 20 });
    await takeScreenshot({ name: 'walk_060_right_360' });
    await press('left', { hold: 90 });
    await wait({ frames: 20 });
    await takeScreenshot({ name: 'walk_070_left_90' });
    await press('up', { hold: 60 });
    await wait({ frames: 20 });
    await takeScreenshot({ name: 'walk_080_up_60' });
    await press('down', { hold: 60 });
    await wait({ frames: 20 });
    await takeScreenshot({ name: 'walk_090_down_60' });
    await press('a', { hold: 12 });
    await wait({ frames: 60 });
    await takeScreenshot({ name: 'walk_100_interact_a' });
    await takeMemorySnapshot({ name: 'io-final', region: 'io' });
    await takeMemorySnapshot({ name: 'iwram-03000000', address: 0x03000000, length: 2048 });
  `;
  await runtime.executeScript(script);
  result.status = 'PASS_RUNTIME_SCRIPT_COMPLETED';
  result.screenshots = runtime.host.generatedFiles.filter((f) => f.startsWith('screenshot'));
  await runtime.writeFinalSaveState();
} catch (err) {
  result.status = 'FAIL_RUNTIME_EXCEPTION';
  result.error = String(err && err.stack ? err.stack : err);
}
await fs.writeFile(path.join(outputDir, 'snakeway-walk-result.json'), JSON.stringify(result, null, 2));
if (result.status.startsWith('FAIL')) {
  console.error(result.error);
  process.exit(1);
}
console.log(result.status);
