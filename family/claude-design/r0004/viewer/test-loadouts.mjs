/** claude-design | Exercise one actual GLB, every loadout and its active controls. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { GLTFLoader } from 'gltf-loader';
import { PresentationController, isAccess, isGear } from './controller.mjs';
import { PoseDriver } from './pose-driver.mjs';
import { LoadoutManager, visibleMeshStats, normalizeModuleScales } from './loadouts.mjs';

globalThis.self=globalThis;
// These stubs allow CPU scene/animation inspection only. No texture or GPU claim.
globalThis.createImageBitmap=async()=>({width:1,height:1,close(){}});
globalThis.ProgressEvent=class extends Event{constructor(type,properties={}){super(type);Object.assign(this,properties);}};
const read=relative=>fs.readFileSync(new URL(relative,import.meta.url));
const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const bytes=read('../models/c130-family.glb'),artBytes=read('../articulation/c130-family.json'),catalogBytes=read('../loadouts/catalog.json');
const art=JSON.parse(artBytes),catalog=JSON.parse(catalogBytes);
assert.equal(hash(bytes),art.sha256,'Master model/sidecar mismatch');
const array=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
const gltf=await new Promise((resolve,reject)=>new GLTFLoader().parse(array,'',resolve,reject));
const scene=gltf.scene,sceneId=scene.uuid;
const moduleNames=new Set(catalog.slots.flatMap(s=>s.options.flatMap(o=>o.module_roots||[])));
const defaultValues=catalog.presets.find(p=>p.id===catalog.default_preset).values;
const defaultNames=new Set(catalog.slots.flatMap(s=>s.options.find(o=>o.id===defaultValues[s.id]).module_roots||[]));
for(const name of moduleNames){const n=scene.getObjectByName(name);assert(n,'Missing module '+name);assert.deepEqual(n.scale.toArray(),defaultNames.has(name)?[1,1,1]:[0,0,0],'Generic-import default scale '+name);}
normalizeModuleScales(scene,catalog);
const driver=new PoseDriver(scene,gltf.animations,art),loadouts=new LoadoutManager(catalog,scene,art);
assert.equal(driver.missing.length,0,JSON.stringify(driver.missing));
const rest=new Map(),identity=new Map();scene.traverse(n=>{rest.set(n.uuid,{node:n,position:n.position.toArray(),quaternion:n.quaternion.toArray(),scale:n.scale.toArray(),morphTargetInfluences:n.morphTargetInfluences?Array.from(n.morphTargetInfluences):null});if(n.isMesh)identity.set(n.uuid,n.geometry);});
let controller=new PresentationController(art),resetError=0;
function assertRest(label){for(const r of rest.values()){for(const [property,values]of [['position',r.position],['quaternion',r.quaternion],['scale',r.scale]]){const now=r.node[property].toArray();for(let i=0;i<now.length;i++){const error=Math.abs(now[i]-values[i]);resetError=Math.max(resetError,error);assert(error<1e-6,label+' '+r.node.name+' '+property);}}if(r.morphTargetInfluences)assert.deepEqual(r.node.morphTargetInfluences,r.morphTargetInfluences,label+' morph reset '+r.node.name);}}
function apply(values){
  const result=loadouts.apply(values,{beforeApply:()=>{controller.reset();driver.apply(controller.snapshot());}});
  controller=new PresentationController(loadouts.activeArticulation());driver.apply(controller.snapshot());
  assertRest('Atomic loadout reset');assert.equal(scene.uuid,sceneId);
  scene.traverse(n=>{if(n.isMesh)assert.equal(n.geometry,identity.get(n.uuid),'Geometry replaced during in-place loadout switch');});
  const expected=new Set(loadouts.options().flatMap(o=>o.module_roots||[]));
  for(const [name,node]of loadouts.roots){
    assert.equal(node.visible,expected.has(name),'Incorrect module choice '+name);
    if(expected.has(name)){let parent=node;while(parent){assert(parent.visible!==false,'Selected module hidden by ancestor: '+name);parent=parent.parent;}}
  }
  const activeOptional=new Set(loadouts.options().flatMap(o=>o.control_ids||[]));
  for(const c of art.controls)assert.equal(controller.byId.has(c.id),!loadouts.optionalControls.has(c.id)||activeOptional.has(c.id),'Inactive control exposed '+c.id);
  return result;
}
apply(defaultValues);
const optionResults=[],presetResults=[],controlChanges={},morphChecks={};
// Every catalogue option must actually change the visible module set in this scene.
for(const slot of catalog.slots)for(const option of slot.options){
  controller.actuateEverything();for(let i=0;i<180;i++)driver.apply(controller.tick(1/60));
  const values={...defaultValues,[slot.id]:option.id};apply(values);
  const decoded=loadouts.parse(loadouts.serialize());assert.deepEqual(decoded,values,'Loadout file round trip');
  optionResults.push({slot:slot.id,option:option.id,modules:option.module_roots||[],active_controls:controller.controls.length,...visibleMeshStats(scene)});
}
const before={selection:{...loadouts.selection},visible:[...loadouts.roots].map(([k,n])=>[k,n.visible])};let invalidCallbackCalled=false;
assert.throws(()=>loadouts.apply({...loadouts.selection,unknown:'invalid'},{beforeApply:()=>{invalidCallbackCalled=true;}}));
assert.equal(invalidCallbackCalled,false,'Invalid loadout reset live mechanisms');
assert.deepEqual(loadouts.selection,before.selection);assert.deepEqual([...loadouts.roots].map(([k,n])=>[k,n.visible]),before.visible);
assert.throws(()=>loadouts.parse({...JSON.parse(loadouts.serialize()),family_id:'another-family'}));
assert.throws(()=>loadouts.parse({...JSON.parse(loadouts.serialize()),revision:'r0000'}));

// Sample actual keyframe tracks. Control declarations alone do not prove movement.
for(const c of art.controls){
  controller.reset();const snapshot=controller.snapshot();let delta=0,morphDelta=0,vertexDelta=0;
  for(const phase of [.25,.5,.75,1]){
    snapshot.values={};snapshot.phases={};snapshot[c.kind==='continuous'?'phases':'values'][c.id]=phase;driver.apply(snapshot);
    for(const t of driver.clips.get(c.clip||c.id).tracks){const r=rest.get(t.node.uuid);for(const [property,values]of [['position',r.position],['quaternion',r.quaternion],['scale',r.scale]]){const now=t.node[property].toArray();for(let i=0;i<now.length;i++)delta=Math.max(delta,Math.abs(now[i]-values[i]));}
      if(t.property==='morphTargetInfluences')for(let i=0;i<t.node.morphTargetInfluences.length;i++){
        const difference=Math.abs(t.node.morphTargetInfluences[i]-(r.morphTargetInfluences?.[i]||0));morphDelta=Math.max(morphDelta,difference);
        const positions=t.node.geometry.morphAttributes.position?.[i],base=t.node.geometry.attributes.position;
        if(positions)for(let j=0;j<positions.count;j++){const x=positions.getX(j)-(t.node.geometry.morphTargetsRelative?0:base.getX(j)),y=positions.getY(j)-(t.node.geometry.morphTargetsRelative?0:base.getY(j)),z=positions.getZ(j)-(t.node.geometry.morphTargetsRelative?0:base.getZ(j));vertexDelta=Math.max(vertexDelta,difference*Math.hypot(x,y,z));}
      }
    }
  }
  assert(Math.max(delta,vertexDelta)>1e-5,'Control has no actual vertex/transform change: '+c.id);controlChanges[c.id]=delta;
  if(morphDelta){assert(vertexDelta>1e-5,'Morph weights do not deform geometry '+c.id);morphChecks[c.id]={maximum_weight_delta:morphDelta,maximum_target_vertex_displacement_m:vertexDelta};}
}
function ownership(snapshot){
  for(const c of controller.controls){
    if(c.owned_by&&snapshot.values[c.id]>.002)assert((snapshot.values[c.owned_by]||0)<=.002,'Conflicting owners '+c.id);
    if(isAccess(c)&&snapshot.values[c.id]>.002)assert(controller.controls.filter(isGear).every(g=>(snapshot.values[g.id]||0)<=.002),'Access during retraction '+c.id);
  }
}
for(const preset of catalog.presets){
  const assessment=apply(preset.values);assert.equal(assessment.preset?.id,preset.id,'Ambiguous duplicate preset configuration');
  assert.equal(assessment.violations.length,0,'Preset violates declared compatibility '+preset.id);
  controller.actuateEverything();
  for(let i=0;i<1500;i++){const snapshot=controller.tick(1/60);ownership(snapshot);driver.apply(snapshot);}
  assert.equal(controller.covered.size,controller.controls.length,'Actuate-everything omitted controls in '+preset.id);
  scene.traverse(n=>assert(n.matrixWorld.elements.every(Number.isFinite),'Non-finite transform '+n.name));
  controller.togglePause();const paused=controller.snapshot(),worlds=new Map();scene.traverse(n=>worlds.set(n.uuid,n.matrixWorld.elements.slice()));
  for(let i=0;i<10;i++)driver.apply(controller.tick(.1));assert.deepEqual(controller.snapshot(),paused,'Pause state changed');
  scene.traverse(n=>assert.deepEqual(n.matrixWorld.elements,worlds.get(n.uuid),'Paused matrix changed'));
  controller.reverse();for(let i=0;i<1500;i++){const snapshot=controller.tick(1/60);ownership(snapshot);driver.apply(snapshot);}
  controller.reset();driver.apply(controller.snapshot());assertRest('Preset reset');
  controller.actuateEverything();for(let i=0;i<1181;i++)driver.apply(controller.tick(1/60));controller.reverse();for(let i=0;i<576;i++){const snapshot=controller.tick(1/60);ownership(snapshot);driver.apply(snapshot);}
  assert(Math.abs(controller.globalTime-(1181-576)/1440)<.002,'Interrupted reverse timeline');
  controller.reset();driver.apply(controller.snapshot());assertRest('Interrupted reset');
  presetResults.push({id:preset.id,label:preset.label,controls:controller.controls.length,coverage:'PASS',pause:'PASS',reverse:'PASS',interrupted_reverse:'PASS',reset:'PASS',...visibleMeshStats(scene)});
}

// Discard an actively firing configuration: no leftover case/flash or motion state.
const firingPreset=catalog.presets.find(p=>loadouts.activeControls(p.values).some(c=>c.kind==='cycle'));
let firingSwitch='NOT_APPLICABLE';
if(firingPreset){
  apply(firingPreset.values);const cycle=controller.controls.find(c=>c.kind==='cycle');controller.fire(cycle.id,3);for(let i=0;i<10;i++)driver.apply(controller.tick(1/60));
  apply(defaultValues);assertRest('Outgoing firing state');assert.equal(Object.keys(controller.firing).length,0);assert.equal(controller.running,false);firingSwitch='PASS';
}
for(const preset of catalog.presets){
  apply(preset.values);for(const c of controller.controls)if(driver.clips.get(c.clip||c.id).tracks.some(t=>t.property==='morphTargetInfluences'))controller.set(c.id,1);
  for(let i=0;i<600;i++)driver.apply(controller.tick(1/60));
  apply(defaultValues);assertRest('Outgoing morph geometry');
}
const testedConstraints=[];
for(const constraint of catalog.constraints||[]){
  const values={...defaultValues};for(const [slot,choices]of Object.entries(constraint.when||{}))values[slot]=Array.isArray(choices)?choices[0]:choices;
  let possible=false;
  for(const [slot,allowed]of Object.entries(constraint.requires||{})){const valid=Array.isArray(allowed)?allowed:[allowed];const alternative=catalog.slots.find(s=>s.id===slot).options.find(o=>!valid.includes(o.id));if(alternative){values[slot]=alternative.id;possible=true;break;}}
  if(possible){const result=apply(values);assert(result.violations.some(v=>v.id===constraint.id),'Compatibility rule not reported '+constraint.id);assert.equal(result.classification,'CUSTOM_JCNC');testedConstraints.push(constraint.id);}
}
apply(defaultValues);
const report={author:'claude-design',revision:'r0004',status:'PASS',model_sha256:hash(bytes),articulation_sha256:hash(artBytes),catalog_sha256:hash(catalogBytes),runtime_hashes:Object.fromEntries(['controller.mjs','pose-driver.mjs','loadouts.mjs','app.mjs'].map(f=>[f,hash(read('./'+f))])),scope:'Three.js 0.170.0 CPU loading of one actual family GLB. Every option, exact preset, active controls, actual clip transform and morph samples, in-place geometry identity, pause/reverse/reset, generic-import default scales, config serialization and outgoing firing/morph reset checked. Texture stubs used; browser/WebGL rendering, photographic accuracy, geometric clearance and native Unreal are NOT_RUN by this test.',one_master_scene:true,generic_import_default:'PASS',normalized_module_roots:moduleNames.size,immutable_mesh_instances:identity.size,options:optionResults,presets:presetResults,actual_control_transform_delta:controlChanges,actual_morph_geometry_samples:morphChecks,invalid_selection_atomicity:'PASS',loadout_file_roundtrip:'PASS',outgoing_firing_reset:firingSwitch,outgoing_morph_reset:'PASS',compatibility_rules_exercised:testedConstraints,reset_max_local_transform_error:resetError};
fs.writeFileSync(new URL('./loadout-runtime-qa.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,model_sha256:report.model_sha256,options:optionResults.length,presets:presetResults.length,controls:art.controls.length,modules:moduleNames.size,reset_error:resetError,scope:report.scope},null,2));
