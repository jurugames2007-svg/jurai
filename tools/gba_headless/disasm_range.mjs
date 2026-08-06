import { HeadlessRuntime } from '@gba-kit/gba-node';
const [,,romPath,addrArg,countArg,modeArg]=process.argv;
const runtime=await HeadlessRuntime.create({romPath, outputDir:'playtest_output/disasm_tmp', logFn:(m)=>console.log(m)});
const addr=Number(addrArg); const count=Number(countArg??80); const mode=modeArg??'thumb';
await runtime.executeScript(`
 const ins=disassemble(${addr}, ${count}, '${mode}');
 for (const i of ins) console.log('0x'+i.address.toString(16).padStart(8,'0'), i.instruction, 'bytes=0x'+i.bytes.toString(16));
`);
