import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
import path from 'node:path';
const romPath = process.argv[2];
const outputDir = process.argv[3] ?? 'playtest_output/long';
const savePath = (process.argv[4] && process.argv[4] !== '-' && process.argv[4] !== 'null') ? process.argv[4] : null;
const cycles = Number(process.argv[5] ?? process.argv[4] ?? 180);
if (!romPath) process.exit(2);
await fs.mkdir(outputDir,{recursive:true});
const result={romPath,outputDir,savePath,cycles,status:'unknown',error:null,screenshots:[]};
try{
 const opts={romPath,outputDir,logFn:()=>{}}; if(savePath) opts.loadSavePath=savePath;
 const runtime=await HeadlessRuntime.create(opts);
 let script=`await wait({frames:30});\nawait takeScreenshot({name:'long_000'});\n`;
 const seq=['a','a','b','start','a','a','right','right','a','down','a','right','a','b'];
 for(let i=0;i<cycles;i++){
  const btn=seq[i%seq.length];
  script += `await press('${btn}', { hold: 8 });\nawait wait({ frames: 30 });\n`;
  if(i%15===14) script += `await takeScreenshot({ name: 'long_${String(i+1).padStart(3,'0')}' });\n`;
 }
 script += `await takeScreenshot({ name: 'final' });\nawait takeMemorySnapshot({ name: 'io-final', region: 'io' });\nawait takeMemorySnapshot({ name: 'iwram-final', address: 0x03000000, length: 4096 });\n`;
 await runtime.executeScript(script);
 result.status='PASS_RUNTIME_SCRIPT_COMPLETED'; result.screenshots=runtime.host.generatedFiles.filter(f=>f.startsWith('screenshot'));
 await runtime.writeFinalSaveState();
}catch(err){result.status='FAIL_RUNTIME_EXCEPTION'; result.error=String(err&&err.stack?err.stack:err);}
await fs.writeFile(path.join(outputDir,'long-result.json'),JSON.stringify(result,null,2));
if(result.status.startsWith('FAIL')){console.error(result.error); process.exit(1);} console.log(result.status);
