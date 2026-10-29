/** claude-design | Exact controller world-matrix samples for independent native rendering. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {GLTFLoader} from 'gltf-loader';
import {PresentationController} from './controller.mjs';
import {PoseDriver} from './pose-driver.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'..'),out=path.join(root,'qa');fs.mkdirSync(out,{recursive:true});
globalThis.self=globalThis;
globalThis.createImageBitmap=async()=>({width:1,height:1,close(){}});
globalThis.ProgressEvent=class extends Event{constructor(t,p={}){super(t);Object.assign(this,p);}};
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const requested=process.argv.slice(2),ids=requested.length?requested:['c130','ac130','ac130j'];
for(const id of ids){
 const source=fs.readFileSync(path.join(root,'models',id+'.glb'));
 const artBytes=fs.readFileSync(path.join(root,'articulation',id+'.json'));
 const art=JSON.parse(artBytes),array=source.buffer.slice(source.byteOffset,source.byteOffset+source.byteLength);
 const gltf=await new Promise((ok,bad)=>new GLTFLoader().parse(array,'',ok,bad));
 const controller=new PresentationController(art),driver=new PoseDriver(gltf.scene,gltf.animations,art);
 if(driver.missing.length)throw new Error(JSON.stringify(driver.missing));
 const samples=[];
 const advance=seconds=>{for(let i=0;i<Math.round(seconds*120);i++)controller.tick(1/120);};
 const capture=label=>{
  const state=controller.snapshot();driver.apply(state);const nodes=[];
  gltf.scene.traverse(n=>{const a=gltf.parser.associations.get(n)||{};if(n===gltf.scene)return;nodes.push({name:n.name,gltf_node_index:a.nodes??null,gltf_mesh_index:a.meshes??null,type:n.type,mesh:Boolean(n.isMesh),matrix_world:n.matrixWorld.toArray(),position:n.position.toArray(),quaternion:n.quaternion.toArray(),scale:n.scale.toArray()});});
  samples.push({label,state,nodes});
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
 controller.reset();capture('RESET');
 const report={author:'claude-design',model:id,model_sha256:hash(source),articulation_sha256:hash(artBytes),controller_sha256:hash(fs.readFileSync(path.join(here,'controller.mjs'))),pose_driver_sha256:hash(fs.readFileSync(path.join(here,'pose-driver.mjs'))),runtime:'Three.js 0.170.0; actual GLB scene and animation tracks',matrix_convention:'Column-major 4x4 world matrices, glTF metres +Y up/nose -Z. To Blender: C*M*C^-1, C maps [x,y,z] to [x,-z,y].',scope:'Exact controller output snapshots. No GPU rendering or geometric-clearance claim.',samples};
 const dest=path.join(out,'viewer-poses-'+id+'.json');fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({id,file:dest,samples:samples.length,nodes:samples[0].nodes.length,model_sha256:report.model_sha256}));
}
