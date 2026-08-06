import { HeadlessRuntime } from '@gba-kit/gba-node';
const [,,romPath,savePath,outDir]=process.argv;
const runtime=await HeadlessRuntime.create({romPath, loadSavePath: savePath, outputDir: outDir, logFn:()=>{}});
await runtime.executeScript(`await takeMemorySnapshot({name:'iwram', region:'iwram'});`);
console.log('done');
