import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
const romPath=process.argv[2]; const out=process.argv[3]??'playtest_output/phase49_menu_controls';
await fs.mkdir(out,{recursive:true});
const runtime=await HeadlessRuntime.create({romPath, outputDir:out, logFn:()=>{}});
const script=`
 await wait({frames:60});
 await takeScreenshot({name:'menu_original'});
 await press('down',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'menu_super'});
 await press('a',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'route_super'});
 await press('b',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'back_to_menu_super'});
 await press('down',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'menu_gt'});
 await press('down',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'menu_af'});
 await press('down',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'menu_log1'});
 await press('a',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'route_log1'});
 await press('b',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'back_to_menu_log1'});
 await press('down',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'menu_log2'});
 await press('a',{hold:8}); await wait({frames:20}); await takeScreenshot({name:'route_log2'});
 await press('start',{hold:8}); await wait({frames:180}); await takeScreenshot({name:'boot_original_after_start'});
`;
let status='PASS', error=null;
try { await runtime.executeScript(script); await runtime.writeFinalSaveState(); } catch(e) { status='FAIL'; error=String(e.stack||e); }
await fs.writeFile(`${out}/gateway-controls-result.json`, JSON.stringify({status,error}, null, 2));
if(status==='FAIL'){ console.error(error); process.exit(1); }
console.log('PASS_RUNTIME_SCRIPT_COMPLETED');
