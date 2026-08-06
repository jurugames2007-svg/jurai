import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
import path from 'node:path';

const romPath = process.argv[2];
const outputDir = process.argv[3] ?? 'playtest_output/trace_dialog_registers';
if (!romPath) {
  console.error('Usage: node trace_dialog_registers.mjs ROM OUTPUT_DIR');
  process.exit(2);
}
await fs.mkdir(outputDir, { recursive: true });
const traces = [];
let status = 'unknown';
let error = null;
try {
  const runtime = await HeadlessRuntime.create({ romPath, outputDir, logFn: () => {} });
  const script = `
    const traces = [];
    const watchA = watchMemory({
      address: 0x0202db00,
      length: 0x900,
      maxHits: 160,
      filter: (h) => {
        if (traces.length < 160) traces.push({ hit: h, regs: getRegisters() });
        return true;
      }
    });
    const seq = ['a','a','b','start','a','a','right','right','a','down','a','right','a','b'];
    await wait({ frames: 30 });
    for (let i = 0; i < 180; i++) {
      const btn = seq[i % seq.length];
      await press(btn, { hold: 8 });
      await wait({ frames: 30 });
    }
    await takeScreenshot({ name: 'trace_final' });
    console.log(JSON.stringify({ count: traces.length, traces: traces.slice(0, 80) }));
  `;
  const logs = [];
  const runtime2 = await HeadlessRuntime.create({ romPath, outputDir, logFn: (m) => logs.push(m) });
  await runtime2.executeScript(script);
  const jsonLine = logs.find((l) => l.startsWith('{"count"')) ?? '{"count":0,"traces":[]}';
  await fs.writeFile(path.join(outputDir, 'dialog-register-trace.json'), JSON.stringify(JSON.parse(jsonLine), null, 2));
  status = 'PASS_RUNTIME_SCRIPT_COMPLETED';
} catch (err) {
  status = 'FAIL_RUNTIME_EXCEPTION';
  error = String(err && err.stack ? err.stack : err);
}
await fs.writeFile(path.join(outputDir, 'trace-result.json'), JSON.stringify({ romPath, status, error }, null, 2));
if (status.startsWith('FAIL')) {
  console.error(error);
  process.exit(1);
}
console.log(status);
