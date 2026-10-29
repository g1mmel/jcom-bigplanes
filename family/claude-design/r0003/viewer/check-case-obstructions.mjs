/** claude-design | Scoped rendered-mesh AABB obstruction probe for repaired case routes. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {GLTFLoader} from 'gltf-loader';
import {PresentationController} from './controller.mjs';
import {PoseDriver} from './pose-driver.mjs';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'..');
globalThis.self=globalThis;globalThis.createImageBitmap=async()=>({width:1,height:1,close(){}});
globalThis.ProgressEvent=class extends Event{constructor(t,p={}){super(t);Object.assign(this,p);}};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const worldBounds=node=>{const b=new THREE.Box3();node.traverse(n=>{if(n.isMesh){const attr=n.geometry.attributes.position;for(let i=0;i<attr.count;i++)b.expandByPoint(new THREE.Vector3().fromBufferAttribute(attr,i).applyMatrix4(n.matrixWorld));}});return b;};
const convexPlanes=node=>{
 const attr=node.geometry.attributes.position,index=node.geometry.index,points=[];
 for(let i=0;i<attr.count;i++)points.push(new THREE.Vector3().fromBufferAttribute(attr,i));
 const center=new THREE.Box3().setFromPoints(points).getCenter(new THREE.Vector3()),planes=[];
 const count=index?index.count:attr.count;
 for(let i=0;i<count;i+=3){const a=points[index?index.getX(i):i],b=points[index?index.getX(i+1):i+1],c=points[index?index.getX(i+2):i+2];
  const n=b.clone().sub(a).cross(c.clone().sub(a));if(n.length()<1e-9)continue;n.normalize();let constant=-n.dot(a);if(n.dot(center)+constant>0){n.negate();constant=-constant;}planes.push({n,constant});
 }return planes;
};
const containedCaseVertices=(caseNode,obstacle)=>{
 const planes=convexPlanes(obstacle),inverse=obstacle.matrixWorld.clone().invert();let count=0,maxDepth=0;
 caseNode.traverse(n=>{if(n.isMesh){const attr=n.geometry.attributes.position;for(let i=0;i<attr.count;i++){
  const point=new THREE.Vector3().fromBufferAttribute(attr,i).applyMatrix4(n.matrixWorld).applyMatrix4(inverse);
  const depth=-Math.max(...planes.map(p=>p.n.dot(point)+p.constant));if(depth>1e-6){count++;maxDepth=Math.max(maxDepth,depth);}
 }}});return {inside_case_vertices:count,maximum_depth_m:maxDepth};
};
const rows=[];
const requested=process.argv.slice(2);
for(const id of requested.length?requested:['ac130','ac130j','gau23-visual','m102-airborne-visual']){
 const component=!['ac130','ac130j'].includes(id),folder=component?path.join(root,'components',id):root;
 const data=fs.readFileSync(component?path.join(folder,'model.glb'):path.join(folder,'models',id+'.glb'));
 const art=JSON.parse(fs.readFileSync(component?path.join(folder,'articulation.json'):path.join(folder,'articulation',id+'.json')));
 assert.equal(hash(data),art.sha256);
 const gltf=await new Promise((ok,bad)=>new GLTFLoader().parse(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'',ok,bad));
 const driver=new PoseDriver(gltf.scene,gltf.animations,art),controller=new PresentationController(art),systems=[];
 for(const c of art.controls.filter(c=>c.kind==='cycle')){
  const gun=c.id.replace(/_fire_cycle$/,''),caseMesh=gltf.scene.getObjectByName(gun+'_SPENT_CASE');assert(caseMesh);
  const names=gun==='gun30'?['gun30_INBOARD_BASE','gun30_BASE_SUPPORT_0','gun30_BASE_SUPPORT_1']:['gun105_INBOARD_BASE','gun105_CASE_EXIT_COVER'];
  const obstacles=names.map(name=>{const node=gltf.scene.getObjectByName(name);assert(node,'Missing obstruction target '+name);return node;});
  const overlaps=[],minimumGaps=Object.fromEntries(names.map(name=>[name,Infinity]));let visibleSamples=0;
  const state=controller.snapshot();
  for(let i=0;i<=128;i++){
   const u=i/128;state.values[c.id]=u;driver.apply(state);
   const scale=caseMesh.getWorldScale(new THREE.Vector3());if(Math.max(...scale.toArray().map(Math.abs))<=.001)continue;
   visibleSamples++;const caseBounds=worldBounds(caseMesh);
   for(const obstacle of obstacles){
    const b=worldBounds(obstacle);
    const sizes=['x','y','z'].map(a=>Math.min(caseBounds.max[a],b.max[a])-Math.max(caseBounds.min[a],b.min[a]));
    const gaps=['x','y','z'].map(a=>Math.max(caseBounds.min[a]-b.max[a],b.min[a]-caseBounds.max[a],0));
    const gap=Math.hypot(...gaps);minimumGaps[obstacle.name]=Math.min(minimumGaps[obstacle.name],gap);
    if(sizes.every(v=>v>1e-6))overlaps.push({u,obstacle:obstacle.name,overlap_axes_m:sizes,aabb_overlap_volume_m3:sizes.reduce((a,b)=>a*b,1),convex_mesh_vertex_containment:containedCaseVertices(caseMesh,obstacle)});
   }
  }
  systems.push({control:c.id,visible_phase_samples:visibleSamples,obstacle_names:names,overlap_count:overlaps.length,potential_overlaps:overlaps,minimum_aabb_gaps_m:minimumGaps,status:overlaps.some(o=>o.convex_mesh_vertex_containment.inside_case_vertices>0)?'CONFIRMED_CONVEX_BASE_VERTEX_INTERPENETRATION':overlaps.length?'POTENTIAL_OVERLAP_REQUIRES_TRIANGLE_REVIEW':'PASS'});
 }
 rows.push({id,model_sha256:hash(data),systems});
}
const report={author:'claude-design',status:rows.every(m=>m.systems.every(s=>s.status==='PASS'))?'PASS':'REVIEW_REQUIRED',scope:'Actual transformed case mesh vertices and named base/support/exit-cover mesh vertices, 129 normalized firing samples with aim at rest. Disjoint AABBs prove no intersection at sampled times. Overlapping AABBs are conservative flags, not proven collisions. For overlaps, actual case vertices are additionally tested against the target convex beveled-box mesh face planes; contained vertices establish real sampled interpenetration. Other geometry and continuous travel are untested.',models:rows};
fs.writeFileSync(path.join(here,'case-obstruction-qa.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,models:rows.map(m=>({id:m.id,systems:m.systems.map(s=>({control:s.control,overlap_count:s.overlap_count,minimum_aabb_gaps_m:s.minimum_aabb_gaps_m}))}))},null,2));
