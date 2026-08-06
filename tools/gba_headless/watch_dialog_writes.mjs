import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
import path from 'node:path';
const romPath=process.argv[2]; const outputDir=process.argv[3]??'playtest_output/watch_dialog';
await fs.mkdir(outputDir,{recursive:true});
const logs=[];
const runtime=await HeadlessRuntime.create({romPath, outputDir, logFn:(m)=>{logs.push(m); console.log(m);}});
const script=`
  const w = watchMemory({ address: 0x0202c000, length: 0x5000, maxHits: 2000, filter: (h)=> h.size>=1 });
  await wait({ frames: 30 });
  await press('start', { hold: 8 }); await wait({ frames: 30 });
  await press('a', { hold: 8 }); await wait({ frames: 30 });
  await press('a', { hold: 8 }); await wait({ frames: 30 });
  await press('start', { hold: 8 }); await wait({ frames: 60 });
  await press('a', { hold: 8 }); await wait({ frames: 60 });
  await press('a', { hold: 8 }); await wait({ frames: 60 });
  await press('a', { hold: 8 }); await wait({ frames: 60 });
  await takeScreenshot({ name: 'after' });
  console.log('hits', w.hits.length);
  const seen = new Map();
  for (const h of w.hits) {
    const k = '0x'+h.instructionAddress.toString(16)+' '+h.source+' thumb='+h.thumb;
    seen.set(k, (seen.get(k)||0)+1);
  }
  for (const [k,c] of [...seen.entries()].sort((a,b)=>b[1]-a[1]).slice(0,80)) console.log(c, k);
  // Log sample hits to text buffer range if any
  let sample=0;
  for (const h of w.hits) {
    if (h.address>=0x0202d800 && h.address<0x0202e300 && sample<80) {
      console.log('sample', sample, 'addr=0x'+h.address.toString(16), 'val=0x'+h.value.toString(16), 'size='+h.size, 'ia=0x'+h.instructionAddress.toString(16), 'pc=0x'+h.pc.toString(16), h.source, 'thumb='+h.thumb);
      sample++;
    }
  }
  await takeMemorySnapshot({ name: 'ewram-watch', region: 'ewram' });
`;
let status='PASS'; let error=null;
try { await runtime.executeScript(script); await runtime.writeFinalSaveState(); } catch(e){ status='FAIL'; error=String(e.stack||e); }
await fs.writeFile(path.join(outputDir,'watch-result.json'), JSON.stringify({status,error,logs},null,2));
if(status==='FAIL'){console.error(error); process.exit(1);} console.log('PASS');
