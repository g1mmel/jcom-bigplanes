/** claude-design | Verify portable dependency closure and lossless model restoration. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const file=process.argv[2]||new URL('./C130-family-portable.html',import.meta.url),bytes=fs.readFileSync(file),html=bytes.toString('utf8');
const payload=JSON.parse(html.match(/<script type="application\/json" id="embedded-assets">([\s\S]*?)<\/script>/)[1]);
const imports=JSON.parse(html.match(/<script type="importmap">([\s\S]*?)<\/script>/)[1]).imports;
const checkedModules=[];
for(const [name,url]of Object.entries(imports)){
 assert(url.startsWith('data:text/javascript;base64,'),'External runtime module '+name);
 const source=Buffer.from(url.split(',')[1],'base64').toString('utf8');
 const module=new vm.SourceTextModule(source,{identifier:name});
 for(const dep of module.dependencySpecifiers)assert(dep in imports,'Unbundled dependency '+dep+' in '+name);
 checkedModules.push(name);
}
const app=html.match(/<script type="module">([\s\S]*?)<\/script>/)[1];
const module=new vm.SourceTextModule(app,{identifier:'app'});for(const dep of module.dependencySpecifiers)assert(dep in imports,'Unbundled app dependency '+dep);
const models=[];
for(const [id,item]of Object.entries(payload.models)){
 const compressed=Buffer.from(item.glb,'base64');
 const restored=item.encoding==='gzip+base64'?new Uint8Array(await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()):compressed;
 const hash=crypto.createHash('sha256').update(restored).digest('hex');assert.equal(hash,item.sha256);
 const source=fs.readFileSync(new URL('../'+(item.source||'models/'+id+'.glb'),import.meta.url));assert.equal(hash,crypto.createHash('sha256').update(source).digest('hex'));
 assert.equal(hash,item.articulation.sha256);models.push({id,bytes:restored.byteLength,sha256:hash});
}
assert(models.length>=1);assert(payload.default_asset in payload.models,'Missing default asset');assert(payload.notes?.length>100,'Missing revision notes');
const report={author:'claude-design',status:'PASS',portable_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length,embedded_modules:checkedModules,models,checks:['All modules parse','All module imports resolve within embedded importmap','Browser-standard gzip DecompressionStream restores exact model bytes','Embedded model hashes equal delivered GLBs and sidecars','Declared assets and revision notes embedded'],scope:'Dependency/byte integrity; browser WebGL rendering NOT_RUN'};
fs.writeFileSync(process.argv[2]?String(process.argv[2])+'.qa.json':new URL('./portable-qa.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
