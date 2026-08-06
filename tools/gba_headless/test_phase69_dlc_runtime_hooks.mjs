import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';

const romPath = process.argv[2];
const out = process.argv[3] ?? 'playtest_output/phase69_dlc_runtime_hooks';
await fs.mkdir(out, { recursive: true });
const runtime = await HeadlessRuntime.create({ romPath, outputDir: out, logFn: () => {} });

const STATE = 0x0203F700;
const tap = async (button, times = 1) => {
  for (let i = 0; i < times; i++) {
    await press(button, { hold: 4 });
    await wait({ frames: 8 });
  }
};

const script = `
  const STATE = ${STATE};
  const tap = ${tap.toString()};
  await wait({frames:60});
  await takeScreenshot({name:'00_gateway_original'});
  await tap('down', 1);
  await tap('a', 1);
  await wait({frames:30});
  await takeScreenshot({name:'01_super_assets_hooked'});
  assert({memory:{address:STATE, equals:0x4c}});
  const magic = read32(STATE);
  const route = read32(STATE + 4);
  const pair = read32(STATE + 8);
  const ptr = read32(STATE + 12);
  console.log('state_super', magic.toString(16), route.toString(16), pair.toString(16), ptr.toString(16));
  if (magic !== 0x4B48344C || route !== 1 || pair !== 0xF001 || ptr === 0) throw new Error('SUPER state/native lookup failed');

  await tap('r', 1); await wait({frames:20}); await takeScreenshot({name:'02_gt_assets_hooked'});
  if (read32(STATE + 4) !== 2 || read32(STATE + 8) !== 0xF002 || read32(STATE + 12) === 0) throw new Error('GT state/native lookup failed');
  await tap('r', 1); await wait({frames:20}); await takeScreenshot({name:'03_af_assets_hooked'});
  if (read32(STATE + 4) !== 3 || read32(STATE + 8) !== 0xF003 || read32(STATE + 12) === 0) throw new Error('AF state/native lookup failed');
  await tap('r', 1); await wait({frames:20}); await takeScreenshot({name:'04_log1_assets_hooked'});
  if (read32(STATE + 4) !== 4 || read32(STATE + 8) !== 0xF004 || read32(STATE + 12) === 0) throw new Error('LOG1 state/native lookup failed');
  await tap('r', 1); await wait({frames:20}); await takeScreenshot({name:'05_log2_assets_hooked'});
  if (read32(STATE + 4) !== 5 || read32(STATE + 8) !== 0xF005 || read32(STATE + 12) === 0) throw new Error('LOG2 state/native lookup failed');
  await takeMemorySnapshot({name:'phase69-state-before-fallback', address: STATE, length: 32});

  await tap('b', 1); await wait({frames:20}); await takeScreenshot({name:'06_back_to_gateway'});
  await tap('a', 1); await wait({frames:20}); await takeScreenshot({name:'07_log2_reentered'});
  await tap('start', 1); await wait({frames:180}); await takeScreenshot({name:'08_original_fallback_after_start'});
  await takeMemorySnapshot({name:'phase69-state', address: STATE, length: 32});
`;
let status = 'PASS', error = null;
try {
  await runtime.executeScript(script);
  await runtime.writeFinalSaveState();
} catch (e) {
  status = 'FAIL';
  error = String(e.stack || e);
}
await fs.writeFile(`${out}/phase69-dlc-runtime-hooks-result.json`, JSON.stringify({ status, error }, null, 2));
if (status === 'FAIL') {
  console.error(error);
  process.exit(1);
}
console.log('PASS_PHASE69_DLC_RUNTIME_HOOKS');
