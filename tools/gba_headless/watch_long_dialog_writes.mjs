import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
import path from 'node:path';
const romPath=process.argv[2]; const outputDir=process.argv[3]??'playtest_output/watch_long_dialog';
await fs.mkdir(outputDir,{recursive:true});
const logs=[];
const runtime=await HeadlessRuntime.create({romPath, outputDir, logFn:(m)=>{logs.push(m); console.log(m);}});
const seq=['a','a','b','start','a','a','right','right','a','down','a','right','a','b'];
let script=`
 const w1=watchMemory({ address: 0x0202db00, length: 0x800, maxHits: 2000 });
 const w2=watchMemory({ address: 0x0202c000, length: 0x200, maxHits: 2000 });
 await wait({ frames: 30 });
 await takeScreenshot({name:'w000'});
`;
for(let i=0;i<260;i++){
 const btn=seq[i%seq.length];
 script += `await press('${btn}', { hold: 8 });\nawait wait({ frames: 30 });\n`;
 if(i%20===19) script += `await takeScreenshot({name:'w${String(i+1).padStart(3,'0')}'});\n`;
}
script += `
 await takeScreenshot({name:'final'});
 console.log('w1hits',w1.hits.length);
 console.log('w2hits',w2.hits.length);
 for (const [name,w] of [['w1',w1],['w2',w2]]) {
  const seen=new Map();
  for (const h of w.hits) { const k='0x'+h.instructionAddress.toString(16)+' '+h.source+' thumb='+h.thumb; seen.set(k,(seen.get(k)||0)+1); }
  console.log('seen',name,seen.size);
  for (const [k,c] of [...seen.entries()].sort((a,b)=>b[1]-a[1]).slice(0,80)) console.log(name,c,k);
  let sample=0;
  for (const h of w.hits) if(sample<80){ console.log(name,'sample',sample,'addr=0x'+h.address.toString(16),'val=0x'+h.value.toString(16),'size='+h.size,'ia=0x'+h.instructionAddress.toString(16),'pc=0x'+h.pc.toString(16),h.source,'thumb='+h.thumb); sample++; }
 }
 await takeMemorySnapshot({ name:'ewram-final', region:'ewram' });
`;
let status='PASS', error=null;
try{ await runtime.executeScript(script); await runtime.writeFinalSaveState(); }catch(e){ status='FAIL'; error=String(e.stack||e); }
await fs.writeFile(path.join(outputDir,'watch-long-result.json'),JSON.stringify({status,error,logs},null,2));
if(status==='FAIL'){ console.error(error); process.exit(1); }
console.log('PASS');
