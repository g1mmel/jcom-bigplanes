/** claude-design | Exact controller world-matrix samples for independent native rendering. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {GLTFLoader} from 'gltf-loader';
import {PresentationController} from './controller.mjs';
import {PoseDriver} from './pose-driver.mjs';
import {LoadoutManager,normalizeModuleScales} from './loadouts.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'..'),out=path.join(root,'qa');fs.mkdirSync(out,{recursive:true});
globalThis.self=globalThis;
globalThis.createImageBitmap=async()=>({width:1,height:1,close(){}});
globalThis.ProgressEvent=class extends Event{constructor(t,p={}){super(t);Object.assign(this,p);}};
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const requested=process.argv.slice(2),ids=requested.length?requested:['c130-family'];
for(const id of ids){
 const component=!fs.existsSync(path.join(root,'models',id+'.glb'));
 const source=fs.readFileSync(component?path.join(root,'components',id,'model.glb'):path.join(root,'models',id+'.glb'));
 const artBytes=fs.readFileSync(component?path.join(root,'components',id,'articulation.json'):path.join(root,'articulation',id+'.json'));
 const art=JSON.parse(artBytes),array=source.buffer.slice(source.byteOffset,source.byteOffset+source.byteLength);
 if(hash(source)!==art.sha256)throw new Error('GLB/sidecar revision mismatch '+id);
 const gltf=await new Promise((ok,bad)=>new GLTFLoader().parse(array,'',ok,bad));
 const catalogue=id==='c130-family'?JSON.parse(fs.readFileSync(path.join(root,'loadouts/catalog.json'),'utf8')):null;
 if(catalogue)normalizeModuleScales(gltf.scene,catalogue);
 const loadouts=catalogue?new LoadoutManager(catalogue,gltf.scene,art):null;
 if(loadouts)loadouts.reset();
 let controller=new PresentationController(loadouts?loadouts.activeArticulation():art);const driver=new PoseDriver(gltf.scene,gltf.animations,art);
 if(driver.missing.length)throw new Error(JSON.stringify(driver.missing));
 const samples=[];
 const advance=seconds=>{for(let i=0;i<Math.round(seconds*120);i++)controller.tick(1/120);};
 const capture=label=>{
  const state=controller.snapshot();driver.apply(state);const nodes=[];
  gltf.scene.traverse(n=>{const a=gltf.parser.associations.get(n)||{};if(n===gltf.scene)return;nodes.push({name:n.name,gltf_node_index:a.nodes??null,gltf_mesh_index:a.meshes??null,type:n.type,mesh:Boolean(n.isMesh),morphTargetInfluences:n.morphTargetInfluences?Array.from(n.morphTargetInfluences):null,visible:n.visible,effective_visible:(()=>{let q=n;while(q){if(q.visible===false)return false;q=q.parent;}return true;})(),matrix_world:n.matrixWorld.toArray(),position:n.position.toArray(),quaternion:n.quaternion.toArray(),scale:n.scale.toArray()});});
  samples.push({label,loadout:loadouts?{...loadouts.selection}:null,state,nodes});
 };
 controller.reset();capture('PARKED');
 controller.preset('SERVICE');advance(12);capture('SERVICE');
 controller.reset();controller.preset('FLYING');advance(12);capture('FLYING');
 controller.reset();controller.actuateEverything();capture('GLOBAL_0');
 advance(controller.globalDuration*.12);capture('GLOBAL_INSPECTION_OPEN');
 advance(controller.globalDuration*.13);capture('GLOBAL_25');
 advance(controller.globalDuration*.17);capture('GLOBAL_ACCESS_OPEN');
 advance(controller.globalDuration*.08);capture('GLOBAL_50');
 advance(controller.globalDuration*.25);capture('GLOBAL_75');
 advance(controller.globalDuration*.25);capture('GLOBAL_100');
 controller.reverse();advance(controller.globalDuration*.5);capture('REVERSE_50');
 for(const c of controller.controls.filter(c=>c.kind==='cycle')){
   const gun=c.id.replace(/_fire_cycle$/,'').toUpperCase();
   for(const phase of [.05,.1,.25,.5,.65,.8]){controller.reset();controller.set(c.id,phase);capture(gun+'_CYCLE_'+Math.round(phase*100));}
 }
 controller.reset();capture('RESET');
 if(loadouts)for(const preset of catalogue.presets){
  controller.reset();driver.apply(controller.snapshot());loadouts.applyPreset(preset.id);controller=new PresentationController(loadouts.activeArticulation());capture('LOADOUT_'+preset.id.toUpperCase());
  controller.actuateEverything();advance(controller.globalDuration*.8);capture('LOADOUT_'+preset.id.toUpperCase()+'_DEMO_80');
  controller.reset();for(const c of controller.controls)if(/tanker.*deploy|skyhook.*deploy|receiver_hatch/.test(c.id))controller.set(c.id,1);advance(20);capture('LOADOUT_'+preset.id.toUpperCase()+'_DEPLOYED');
  if(controller.byId.has('jato_burn')){controller.reset();controller.set('jato_burn',.25);capture('LOADOUT_'+preset.id.toUpperCase()+'_JATO_25');}
  for(const c of controller.controls.filter(c=>/^gun(30|105)_fire_cycle$/.test(c.id))){controller.reset();controller.set(c.id,.5);capture('LOADOUT_'+preset.id.toUpperCase()+'_'+c.id.toUpperCase()+'_50');}
  if(preset.id===catalogue.default_preset){controller.reset();controller.preset('SERVICE');advance(12);capture('DEFAULT_SERVICE');}
 }
 const report={author:'claude-design',model:id,model_sha256:hash(source),articulation_sha256:hash(artBytes),loadout_catalog_sha256:catalogue?hash(fs.readFileSync(path.join(root,'loadouts/catalog.json'))):null,controller_sha256:hash(fs.readFileSync(path.join(here,'controller.mjs'))),pose_driver_sha256:hash(fs.readFileSync(path.join(here,'pose-driver.mjs'))),runtime:'Three.js 0.170.0; actual GLB scene and animation tracks',matrix_convention:'Column-major 4x4 world matrices, glTF metres +Y up/nose -Z. To Blender: C*M*C^-1, C maps [x,y,z] to [x,-z,y].',scope:'Exact controller output snapshots. No GPU rendering or geometric-clearance claim.',samples};
 const dest=path.join(out,'viewer-poses-'+id+'.json');fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({id,file:dest,samples:samples.length,nodes:samples[0].nodes.length,model_sha256:report.model_sha256}));
}
