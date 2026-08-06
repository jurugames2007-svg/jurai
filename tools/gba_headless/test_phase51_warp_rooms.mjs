import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';

const romPath = process.argv[2];
const out = process.argv[3] ?? 'playtest_output/phase51_warp_rooms';
await fs.mkdir(out, { recursive: true });
const runtime = await HeadlessRuntime.create({ romPath, outputDir: out, logFn: () => {} });

const tap = async (button, times = 1) => {
  for (let i = 0; i < times; i++) {
    await press(button, { hold: 4 });
    await wait({ frames: 8 });
  }
};

const script = `
  const tap = ${tap.toString()};
  await wait({frames:60});
  await takeScreenshot({name:'00_gateway_original'});

  // Enter SUPER room.
  await tap('down', 1);
  await takeScreenshot({name:'01_gateway_super_selected'});
  await tap('a', 1);
  await wait({frames:20});
  await takeScreenshot({name:'02_super_room_spawn'});

  // Move around the room to prove the marker is live.
  await tap('left', 4);
  await tap('up', 4);
  await takeScreenshot({name:'03_super_marker_moved'});

  // L/R room cycling.
  await tap('r', 1);
  await wait({frames:20});
  await takeScreenshot({name:'04_gt_room_after_r'});
  await tap('r', 3);
  await wait({frames:20});
  await takeScreenshot({name:'05_log1_room_after_r_cycle'});

  // Navigate to NEXT pad in the LOG1 room and activate it to warp to LOG2.
  await tap('down', 3);
  await tap('right', 14);
  await takeScreenshot({name:'06_log1_on_next_pad'});
  await tap('a', 1);
  await wait({frames:20});
  await takeScreenshot({name:'07_log2_after_next_pad'});

  // Navigate to HOME pad and activate it to return to the Gateway menu.
  await tap('left', 14);
  await tap('down', 3);
  await takeScreenshot({name:'08_log2_on_home_pad'});
  await tap('a', 1);
  await wait({frames:20});
  await takeScreenshot({name:'09_gateway_returned_from_home'});

  // Re-enter LOG2 then press Start to prove original fallback still boots.
  await tap('a', 1);
  await wait({frames:20});
  await takeScreenshot({name:'10_log2_reentered'});
  await tap('start', 1);
  await wait({frames:180});
  await takeScreenshot({name:'11_original_boot_after_start'});
`;

let status = 'PASS', error = null;
try {
  await runtime.executeScript(script);
  await runtime.writeFinalSaveState();
} catch (e) {
  status = 'FAIL';
  error = String(e.stack || e);
}
await fs.writeFile(`${out}/phase51-warp-rooms-result.json`, JSON.stringify({ status, error }, null, 2));
if (status === 'FAIL') {
  console.error(error);
  process.exit(1);
}
console.log('PASS_PHASE51_WARP_ROOMS_RUNTIME_SCRIPT_COMPLETED');
