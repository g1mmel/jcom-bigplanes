/** claude-design | Exercise real exported firing clips and their physical case nodes. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import * as THREE from 'three';
import {GLTFLoader} from 'gltf-loader';
import {PresentationController} from './controller.mjs';
import {PoseDriver} from './pose-driver.mjs';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'..');
globalThis.self=globalThis;
globalThis.createImageBitmap=async()=>({width:1,height:1,close(){}});
globalThis.ProgressEvent=class extends Event{constructor(t,p={}){super(t);Object.assign(this,p);}};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const ids=process.argv.slice(2).length?process.argv.slice(2):['ac130','ac130j','gau23-visual','m102-airborne-visual'];
const rows=[];
for(const id of ids){
 const component=!['c130','ac130','ac130j'].includes(id);
 const glbPath=component?path.join(root,'components',id,'model.glb'):path.join(root,'models',id+'.glb');
 const artPath=component?path.join(root,'components',id,'articulation.json'):path.join(root,'articulation',id+'.json');
 const data=fs.readFileSync(glbPath),artBytes=fs.readFileSync(artPath),art=JSON.parse(artBytes);
 assert.equal(hash(data),art.sha256);
 const gltf=await new Promise((ok,bad)=>new GLTFLoader().parse(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'',ok,bad));
 const driver=new PoseDriver(gltf.scene,gltf.animations,art),controller=new PresentationController(art);
 assert.equal(driver.missing.length,0);
 const cycles=art.controls.filter(c=>c.kind==='cycle');assert(cycles.length,'No firing cycles exported for '+id);
 const profiles=Array.isArray(art.firing_profiles)?art.firing_profiles:Object.values(art.firing_profiles||{});
 const systems=[];
 for(const c of cycles){
   const gun=c.id.replace(/_fire_cycle$/,'');
   const profile=profiles.find(p=>(p.control_id||p.control)===c.id)||{};
   const ejection=gltf.scene.getObjectByName(profile.ejection_socket||gun+'_CASE_EJECT_SOCKET');
   const muzzle=gltf.scene.getObjectByName(profile.muzzle_socket||gun+'_MUZZLE_VISUAL_SOCKET');
   assert(ejection,'Missing internal case socket '+c.id);assert(muzzle,'Missing muzzle socket '+c.id);
   let caseNode=profile.case_node?gltf.scene.getObjectByName(profile.case_node):null;
   if(!caseNode)gltf.scene.traverse(n=>{if(!caseNode&&n.name.startsWith(gun)&&/SPENT_CASE|CASING|CASE_BODY/.test(n.name))caseNode=n;});
   assert(caseNode,'Missing separately modeled spent-case node '+c.id);
   let caseVertices=0;caseNode.traverse(n=>{if(n.isMesh)caseVertices+=n.geometry.attributes.position.count;});
   assert(caseVertices>0,'Case node lacks physical mesh '+caseNode.name);
   const mount=gltf.scene.getObjectByName('PIVOT_'+gun+'_component');
   assert(mount,'Missing component datum for inboard plane check '+gun);
   const clip=driver.clips.get(c.clip||c.id);assert(clip.tracks.length>=2,'Incomplete firing animation '+c.id);
   controller.reset();const state=controller.snapshot();const samples=[];
   for(const t of Array.from({length:65},(_,i)=>i/64)){
     state.values[c.id]=t;driver.apply(state);
     const center=caseNode.getWorldPosition(new THREE.Vector3());
     const scale=caseNode.getWorldScale(new THREE.Vector3());
     const visible=Math.max(...scale.toArray().map(Math.abs))>.001;
     samples.push({u:t,case_visible:visible,case_world:visible?center.toArray():null,case_world_scale:scale.toArray(),muzzle_world:muzzle.getWorldPosition(new THREE.Vector3()).toArray()});
     assert([...center,...scale].every(Number.isFinite));
   }
   const positions=samples.filter(s=>s.case_visible).map(s=>new THREE.Vector3(...s.case_world));
   assert(positions.length>=2,'No visible spent-case sequence '+c.id);
   const travel=Math.max(...positions.map(p=>p.distanceTo(positions[0])));
   assert(travel>1e-4,'Physical spent case does not move '+c.id);
   let minimumInboard=Infinity,minimumWorldX=Infinity,maximumWorldX=-Infinity,visibleVertexSamples=0;
   const caseMeshes=[];caseNode.traverse(n=>{if(n.isMesh)caseMeshes.push(n);});
   for(const yaw of [0,.5,1])for(const pitch of [0,.5,1]){
     const combined=controller.snapshot();combined.values[gun+'_yaw']=yaw;combined.values[gun+'_pitch']=pitch;
     for(let frame=0;frame<=64;frame++){
       combined.values[c.id]=frame/64;driver.apply(combined);
       const scale=caseNode.getWorldScale(new THREE.Vector3());
       if(Math.max(...scale.toArray().map(Math.abs))<=.001)continue;
       const toMount=mount.matrixWorld.clone().invert();
       for(const mesh of caseMeshes){
         const attr=mesh.geometry.attributes.position;
         for(let vi=0;vi<attr.count;vi++){
           const world=new THREE.Vector3().fromBufferAttribute(attr,vi).applyMatrix4(mesh.matrixWorld);
           minimumWorldX=Math.min(minimumWorldX,world.x);maximumWorldX=Math.max(maximumWorldX,world.x);
           const local=world.clone().applyMatrix4(toMount);minimumInboard=Math.min(minimumInboard,local.x);visibleVertexSamples++;
         }
       }
     }
   }
   assert(minimumInboard>=-1e-6,'A visible spent-case vertex crosses outboard of component aperture plane '+id+'/'+gun+': '+minimumInboard);
   controller.reset();controller.fire(c.id,gun==='gun30'?3:1);
   const advance=dt=>{for(let i=0;i<Math.round(dt*120);i++)driver.apply(controller.tick(1/120));};
   advance(.2);controller.togglePause();driver.apply(controller.snapshot());
   const held=new Map();gltf.scene.traverse(n=>held.set(n.uuid,n.matrixWorld.elements.slice()));advance(.3);
   gltf.scene.traverse(n=>assert.deepEqual(n.matrixWorld.elements,held.get(n.uuid),'Pause moved '+n.name));
   controller.togglePause();advance(.1);const before=new Map();gltf.scene.traverse(n=>before.set(n.uuid,n.matrixWorld.elements.slice()));
   controller.reverse();advance(.05);controller.reverse();advance(.05);
   let error=0;gltf.scene.traverse(n=>n.matrixWorld.elements.forEach((v,i)=>{error=Math.max(error,Math.abs(v-before.get(n.uuid)[i]));}));
   assert(error<1e-5,'Interrupted reverse drift '+error);
   controller.reset();driver.apply(controller.snapshot());
   assert(Math.max(...caseNode.getWorldScale(new THREE.Vector3()).toArray().map(Math.abs))<=.001,'Reset left a ghost spent case '+caseNode.name);
   controller.actuateEverything();advance(11.8);controller.fire(c.id,1);driver.apply(controller.snapshot());
   assert(Math.max(...caseNode.getWorldScale(new THREE.Vector3()).toArray().map(Math.abs))<=.001,'Manual fire did not restart the physical case at hidden rest');
   controller.reset();driver.apply(controller.snapshot());
   systems.push({control:c.id,case_node:caseNode.name,physical_case_vertices:caseVertices,visible_case_movement_m:travel,hidden_case_tracking:'omitted while scale <= .001',inboard_vertex_check:{status:'PASS',plane:'Component datum local x=0, inboard +X',minimum_distance_m:minimumInboard,world_x_range:[minimumWorldX,maximumWorldX],visible_vertex_samples:visibleVertexSamples,pose_grid:'3 yaw × 3 pitch × 65 firing phases',limitation:'This establishes the inboard side of the mount plane only, not complete cabin collision clearance.'},reset_case_hidden:'PASS',tracks:clip.tracks.length,samples,pause:'PASS',reverse_phase_matrix_error:error,muzzle_socket:muzzle.name,ejection_socket:ejection.name,collection:profile.collection||'See component evidence'});
 }
 rows.push({id,sha256:hash(data),articulation_sha256:hash(artBytes),systems});
}
const report={author:'claude-design',status:'PASS',models:rows,controller_sha256:hash(fs.readFileSync(path.join(here,'controller.mjs'))),pose_driver_sha256:hash(fs.readFileSync(path.join(here,'pose-driver.mjs'))),scope:'Actual Three.js GLB parsing and physical case/recoil/FX animation tracks, sampled world positions, pause and interrupted reverse. Texture decoding is stubbed; browser rendering, continuous collisions, real weapon operation and native Unreal are NOT_RUN.'};
fs.writeFileSync(path.join(here,'firing-model-qa.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,models:rows.map(r=>({id:r.id,systems:r.systems.length,sha256:r.sha256}))},null,2));
