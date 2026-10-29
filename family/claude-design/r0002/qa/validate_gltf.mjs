/** Official Khronos glTF validator; pinned by qa/package-lock.json. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import validator from 'gltf-validator';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(process.argv[2]||path.join(here,'..'));
const ids=process.argv.slice(3).length?process.argv.slice(3):['c130','ac130','ac130j'];
const summary={
  generated_utc:new Date().toISOString(),
  tool:'KhronosGroup/glTF-Validator',
  upstream:'https://github.com/KhronosGroup/glTF-Validator',
  npm_package:'gltf-validator',
  pinned_version:'2.0.0-dev.3.10',
  actual_version:validator.version(),
  npm_integrity:'sha512-odJ4k0tRkGXiDGn78yDBg+fBbAIvBnXxh3RwAta0emSxGtyagFE8B4xELB1oYe3S5RD8Ci3uZAsZaascH2LAEQ==',
  node_version:process.version,
  scope:'glTF2.0/GLB format, schema, references, binary/accessor/animation data and embedded resources. Does not establish visual accuracy, collision clearance, license or native engine acceptance.',
  models:[]
};
let failed=false;
for(const id of ids){
  const file=path.join(root,'models',`${id}.glb`);
  const data=await fs.readFile(file);
  const hash=crypto.createHash('sha256').update(data).digest('hex');
  const report=await validator.validateBytes(new Uint8Array(data),{
    uri:`models/${id}.glb`,
    maxIssues:0,
    externalResourceFunction:async(uri)=>{
      const resolved=path.resolve(path.dirname(file),uri);
      if(!resolved.startsWith(root+path.sep))throw new Error('External resource outside package');
      return new Uint8Array(await fs.readFile(resolved));
    }
  });
  const output={input:{file:`models/${id}.glb`,bytes:data.byteLength,sha256:hash},validator_report:report};
  await fs.writeFile(path.join(here,`${id}.gltf-validator.json`),JSON.stringify(output,null,2)+'\n');
  const codes={}; for(const message of report.issues.messages)codes[message.code]=(codes[message.code]||0)+1;
  const result={id,...output.input,status:report.issues.numErrors?'FAIL':'PASS',
    errors:report.issues.numErrors,warnings:report.issues.numWarnings,infos:report.issues.numInfos,hints:report.issues.numHints,
    messages_truncated:report.issues.truncated,issue_codes:codes,report:`qa/${id}.gltf-validator.json`};
  summary.models.push(result); if(result.errors)failed=true;
}
summary.status=failed?'FAIL':'PASS';
await fs.writeFile(path.join(here,'gltf-validator-summary.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));
if(failed)process.exitCode=1;
