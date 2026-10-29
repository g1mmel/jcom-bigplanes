/** claude-design | Actual Three.js loader/clip/pose QA; textures are not GPU rendered. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import * as THREE from 'three';
import { GLTFLoader } from 'gltf-loader';
 import { PresentationController, isGear, isAccess } from './controller.mjs';
import { PoseDriver } from './pose-driver.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
globalThis.self=globalThis;
// Only animation/scene loading is tested. Image dimensions are deliberately stubbed;
// this test never claims texture, material, WebGL, or browser rendering acceptance.
globalThis.createImageBitmap=async()=>({width:1,height:1,close(){}});
globalThis.ProgressEvent=class extends Event{constructor(t,p={}){super(t);Object.assign(this,p);}};
const results=[];
const requested=process.argv.slice(2),ids=requested.length?requested:['c130','ac130','ac130j','gau23-visual','m102-airborne-visual','eoir-visual'];
for(const id of ids){
 const component=!['c130','ac130','ac130j'].includes(id);
 const artPath=component?path.join(root,'../components',id,'articulation.json'):path.join(root,'../articulation',id+'.json');
 const p=component?path.join(root,'../components',id,'model.glb'):path.join(root,'../models',id+'.glb');const data=fs.readFileSync(p);
 const art=JSON.parse(fs.readFileSync(artPath,'utf8'));
 assert.equal(crypto.createHash('sha256').update(data).digest('hex'),art.sha256,'GLB/sidecar revision mismatch');
 const array=data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength);
 const gltf=await new Promise((ok,bad)=>new GLTFLoader().parse(array,'',ok,bad));
 const controller=new PresentationController(art),driver=new PoseDriver(gltf.scene,gltf.animations,art);
 assert.equal(driver.missing.length,0,JSON.stringify(driver.missing));
 const rests=new Map();gltf.scene.updateMatrixWorld(true);gltf.scene.traverse(n=>rests.set(n.uuid,n.matrixWorld.elements.slice()));
 const changes={};
 for(const c of art.controls){
   controller.reset();const state=controller.snapshot();let maximum=0;
   for(const t of [.25,.5,.75,1]){
    if(c.kind==='continuous')state.phases[c.id]=t;else state.values[c.id]=t;
    driver.apply(state);
    gltf.scene.traverse(n=>{const r=rests.get(n.uuid);for(let j=0;j<16;j++)maximum=Math.max(maximum,Math.abs(r[j]-n.matrixWorld.elements[j]));});
   }
   changes[c.id]=maximum;assert(maximum>1e-5,'Control did not transform scene: '+id+'/'+c.id);
 }
 controller.reset();controller.actuateEverything();let finite=true;
 const checkOwnership=s=>{for(const c of art.controls){if(c.owned_by&&(s.values[c.id]||0)>.002)assert((s.values[c.owned_by]||0)<=.002,'Conflicting transform owners '+c.id);if(isAccess(c)&&(s.values[c.id]||0)>.002)assert(art.controls.filter(isGear).every(g=>(s.values[g.id]||0)<=.002),'Access during gear transition '+c.id);}};
 for(let frame=0;frame<1500;frame++){
   const state=controller.tick(1/60);checkOwnership(state);driver.apply(state);
   gltf.scene.traverse(n=>{if(!n.matrixWorld.elements.every(Number.isFinite))finite=false;});
 }
 assert(finite,'Nonfinite pose transform');assert.equal(controller.covered.size,art.controls.length,'Global coverage '+id);
 controller.togglePause();const paused=controller.snapshot();driver.apply(paused);const matrices=new Map();gltf.scene.traverse(n=>matrices.set(n.uuid,n.matrixWorld.elements.slice()));
 controller.tick(.1);driver.apply(controller.snapshot());gltf.scene.traverse(n=>assert.deepEqual(n.matrixWorld.elements,matrices.get(n.uuid),'Pause failed '+n.name));
 controller.reverse();for(let i=0;i<1500;i++){const state=controller.tick(1/60);checkOwnership(state);driver.apply(state);}
 controller.reset();controller.actuateEverything();for(let i=0;i<Math.round(controller.globalDuration*.82*60);i++)driver.apply(controller.tick(1/60));
 const interrupted=controller.snapshot();if(art.controls.some(isGear))assert(art.controls.filter(isGear).some(g=>interrupted.values[g.id]>.1&&interrupted.values[g.id]<.99),'Expected intermediate master pose');
 controller.reverse();for(let i=0;i<Math.round(controller.globalDuration*.4*60);i++){const state=controller.tick(1/60);checkOwnership(state);driver.apply(state);}
 assert(Math.abs(controller.globalTime-.42)<.002,'Interrupted reverse timeline');assert(art.controls.filter(isGear).every(g=>controller.values[g.id]===0),'Gear must recover before cargo reopens');
 controller.reset();driver.apply(controller.snapshot());let resetError=0;gltf.scene.traverse(n=>{const r=rests.get(n.uuid);for(let j=0;j<16;j++)resetError=Math.max(resetError,Math.abs(r[j]-n.matrixWorld.elements[j]));});
 assert(resetError<1e-6,'Reset drift');
 results.push({id,model_sha256:crypto.createHash('sha256').update(data).digest('hex'),articulation_sha256:crypto.createHash('sha256').update(fs.readFileSync(artPath)).digest('hex'),clips:gltf.animations.length,controls:art.controls.length,bindings:'PASS',control_transform_deltas:changes,combined_transform_finiteness:'PASS',global_coverage:controller.controls.length,master_ownership_arbitration:'PASS',interrupted_master_reverse:'PASS',pause:'PASS',reset_max_matrix_error:resetError});
}
const report={author:'claude-design',scope:'Actual GLB loading and node animation with Three.js 0.170.0. No browser/WebGL, texture rendering, native Unreal, or geometric clearance acceptance.',status:'PASS',controller_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'controller.mjs'))).digest('hex'),pose_driver_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'pose-driver.mjs'))).digest('hex'),models:results};
fs.writeFileSync(path.join(root,'model-runtime-qa.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
