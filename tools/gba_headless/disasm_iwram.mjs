import { HeadlessRuntime } from '@gba-kit/gba-node';
import fs from 'node:fs/promises';
const [,,romPath,savePath,outDir]=process.argv;
await fs.mkdir(outDir,{recursive:true});
const runtime=await HeadlessRuntime.create({romPath, loadSavePath: savePath, outputDir: outDir, logFn:(m)=>console.log(m)});
await runtime.executeScript(`
 for (const addr of [0x03000040,0x03000060,0x03000240,0x03000268,0x0807b7a04,0x0807b7c0c]) {
   console.log('DISASM 0x'+addr.toString(16));
   const ins=disassemble(addr, 24, 'arm');
   for (const i of ins) console.log('0x'+i.address.toString(16), i.instruction, i.bytes);
 }
`);
