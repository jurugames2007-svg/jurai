import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
const romPath = process.argv[2];
const out = process.argv[3] ?? 'playtest_output/phase78_dlc_action_hooks';
await fs.mkdir(out, { recursive: true });
const runtime = await HeadlessRuntime.create({ romPath, outputDir: out, logFn: () => {} });
const STATE = 0x0203F700;
const tap = async (button, times = 1) => { for (let i=0; i<times; i++) { await press(button, {hold:4}); await wait({frames:8}); } };
const script = `
 const STATE = ${STATE};
 const tap = ${tap.toString()};
 await wait({frames:60});
 await tap('down', 1); await tap('a', 1); await wait({frames:20});
 await takeScreenshot({name:'00_super_frame0'});
 if (read32(STATE) !== 0x4B48344C || read32(STATE+4) !== 1 || read32(STATE+8) !== 0xF001 || read32(STATE+12) === 0 || read32(STATE+16) !== 0) throw new Error('frame0 state failed');
 await tap('select', 1); await wait({frames:20}); await takeScreenshot({name:'01_super_frame1'});
 if (read32(STATE+16) !== 1) throw new Error('frame1 action failed');
 await tap('select', 1); await wait({frames:20}); await takeScreenshot({name:'02_super_frame2'});
 if (read32(STATE+16) !== 2) throw new Error('frame2 action failed');
 await tap('select', 1); await wait({frames:20}); await takeScreenshot({name:'03_super_frame0_again'});
 if (read32(STATE+16) !== 0) throw new Error('frame reset action failed');
 await tap('r', 4); await wait({frames:20}); await takeScreenshot({name:'04_log2_frame0'});
 if (read32(STATE+4) !== 5 || read32(STATE+8) !== 0xF005 || read32(STATE+12) === 0 || read32(STATE+16) !== 0) throw new Error('LOG2 state failed');
 await takeMemorySnapshot({name:'phase78-route-state', address: STATE, length: 32});
 await tap('start', 1); await wait({frames:240}); await takeScreenshot({name:'05_original_fallback_after_start'});
 await takeMemorySnapshot({name:'phase78-native-lookup-trace', address: 0x0203F740, length: 0x120});
`;
let status='PASS', error=null;
try { await runtime.executeScript(script); await runtime.writeFinalSaveState(); } catch(e) { status='FAIL'; error=String(e.stack||e); }
await fs.writeFile(`${out}/phase78-dlc-action-hooks-result.json`, JSON.stringify({status,error}, null, 2));
if(status==='FAIL') { console.error(error); process.exit(1); }
console.log('PASS_PHASE78_DLC_ACTION_HOOKS');
