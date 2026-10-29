#!/usr/bin/env python3
"""claude-design: self-contained independent-system inspectors and scoped offline QA.

Each generated HTML embeds only its component GLB, articulation and pinned runtime.
The isolated verification extracts those embedded files into a temporary directory.
No aircraft geometry, network connection, browser, or Unreal runtime is used.
"""
from pathlib import Path
import argparse, base64, gzip, hashlib, html, json, re, subprocess, tempfile

HERE=Path(__file__).resolve().parent
REV=HERE.parent
COMPONENTS={
    'hose-drogue-left':'Left hose-and-drogue system',
    'hose-drogue-right':'Right hose-and-drogue system',
    'fulton-yoke':'Fulton recovery yoke',
    'jato-kit':'Historical JATO visual kit',
}
MODULES={'three':'vendor/three.module.js','c130-controller':'controller.mjs','c130-pose-driver':'pose-driver.mjs','gltf-loader':'vendor/GLTFLoader.js','orbit-controls':'vendor/OrbitControls.js','c130-buffer-utils':'vendor/BufferGeometryUtils.js'}
def sha(data):return hashlib.sha256(data).hexdigest()

STYLE=r'''
:root{font-family:Inter,"Segoe UI",Arial,sans-serif;color:#e0ebf0;background:#09121a;--muted:#8ca6b5;--line:#29404d;--teal:#8ee1ca}*{box-sizing:border-box}body{margin:0}button,input,select{font:inherit}button,select{background:#172a35;color:#d4e5ee;border:1px solid #35515f;border-radius:5px;cursor:pointer;padding:9px 12px;font-size:11px}button:hover,select:hover{background:#23404c}button:focus-visible,select:focus-visible,input:focus-visible,a:focus-visible{outline:2px solid var(--teal);outline-offset:3px}button.selected{color:var(--teal);border-color:#659d90;background:#163c31}button.primary{background:var(--teal);color:#092d23;border-color:var(--teal);font-weight:650}button:disabled{opacity:.4;cursor:not-allowed}header{height:66px;display:flex;justify-content:space-between;align-items:center;padding:0 25px;border-bottom:1px solid var(--line);gap:15px}.brand{font-size:16px;letter-spacing:2px;font-weight:700}.brand small{font-size:9px;color:var(--muted);margin-left:15px;font-weight:500}.revision{font-size:10px;color:#d6bc85;letter-spacing:1px}main{display:grid;grid-template-columns:minmax(0,1fr) 300px;min-height:calc(100vh - 107px)}.workspace{padding:22px;min-width:0}.component-title{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:15px}h1{font-size:20px;font-weight:550;margin:0}.component-title small{font-size:9px;color:var(--muted);white-space:nowrap}.stage{position:relative;height:calc(100vh - 260px);min-height:420px;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:radial-gradient(ellipse at 45% 35%,#17323f,#0b1a25 75%)}canvas{display:block;width:100%;height:100%;cursor:grab}.stats{position:absolute;top:18px;right:20px;text-align:right;font-size:10px;color:#aec7d4;pointer-events:none}.stats small{display:block;color:#7191a3;font-size:9px;margin-top:6px}.unit-label{position:absolute;left:20px;top:20px;color:#8fbaa9;font-size:9px;letter-spacing:1px;pointer-events:none}.cameras{display:flex;flex-direction:column;gap:5px;position:absolute;top:66px;left:15px}.cameras button{font-size:10px;padding:6px 8px;backdrop-filter:blur(3px);background:#112430c9}.hint{position:absolute;left:20px;bottom:17px;color:#6f91a4;font-size:9px;pointer-events:none}.loading{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#0c1d28ee;z-index:2;font-size:12px;color:#aed7df;padding:25px;text-align:center}.toolbar{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:13px}.mode-buttons{display:flex;gap:3px;margin-left:auto}.mode-buttons button{font-size:9px;padding:8px 10px}.status{font-size:10px;color:#7fa494;margin-top:12px;line-height:1.6;min-height:18px}.aside{padding:26px 21px;border-left:1px solid var(--line);background:#0d1d27;max-height:calc(100vh - 107px);overflow:auto;scrollbar-width:thin}.eyebrow{font-size:8px;letter-spacing:1.5px;color:#6f96a9}h2{font-size:22px;font-weight:500;margin:5px 0 14px}.intro,.note{font-size:11px;line-height:1.65;color:#8eabbc}.control{border-top:1px solid var(--line);padding:19px 0}.control label{font-size:12px;display:flex;justify-content:space-between;gap:9px;color:#bdd3df}.control output{font-size:11px;color:var(--teal);font-family:Consolas,monospace;min-width:37px;text-align:right}.control input{width:100%;accent-color:var(--teal);margin:16px 0 9px;cursor:pointer}.endpoints{display:flex;justify-content:space-between;gap:12px;font-size:9px;line-height:1.5;color:#7293a6}.basket-label{display:block;font-size:10px;color:#b7d0db;margin:17px 0}.basket-label select{width:100%;margin-top:7px}.basket-label small{display:block;font-size:9px;line-height:1.5;color:#7899a9;margin-top:7px}.cycle-button{width:100%;margin-top:14px;color:#e8cd98;background:#352f21;border-color:#81704c}details{border-top:1px solid var(--line);padding-top:15px;margin-top:20px;font-size:10px;color:#8caabc}summary{cursor:pointer;font-size:11px;color:#b6cdd8}details p{font-size:10px;line-height:1.65}a{color:#9ed7cf;word-break:break-word}code{font-size:9px;word-break:break-all;color:#90b1c1}.evidence-link{margin:9px 0;font-size:10px;line-height:1.5}footer{height:41px;border-top:1px solid var(--line);padding:0 25px;display:flex;justify-content:space-between;align-items:center;color:#587b91;font-size:9px}.error{color:#efb49e}.error p{line-height:1.7}[hidden]{display:none!important}@media(max-width:1000px){main{grid-template-columns:minmax(0,1fr) 260px}.workspace{padding:17px}.aside{padding:22px 17px}.toolbar{gap:5px}.mode-buttons{width:100%;margin:4px 0 0}.component-title{display:block}.component-title small{display:block;margin-top:7px}}@media(max-width:740px){header{padding:0 16px;height:60px}.brand small{display:none}.revision{font-size:8px}main{display:block}.workspace{padding:15px 12px}.stage{height:55vh;min-height:360px}.aside{max-height:none;border-left:0;border-top:1px solid var(--line);padding:23px}.toolbar>button{flex:1;font-size:10px;padding:10px 7px}.toolbar>button.primary{flex:2}.mode-buttons button{flex:1}.unit-label{max-width:44%;font-size:7px;line-height:1.5}.stats{font-size:9px}.hint{font-size:8px}.component-title h1{font-size:18px}footer{font-size:8px;padding:0 15px}footer>span:last-child{display:none}}
'''

TEMPLATE=r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>JCNC · __TITLE__</title><style>__STYLE__</style><script type="importmap">__IMPORTMAP__</script></head><body>
<header><div class="brand">JCNC <small>COMPONENT LAB</small></div><div class="revision">INDEPENDENT SYSTEM / r0004</div></header>
<main><section class="workspace"><div class="component-title"><h1>__TITLE__</h1><small>SELF-CONTAINED · LEVEL 1</small></div><div class="stage" id="stage"><canvas id="scene" aria-label="Interactive independent system"></canvas><div class="loading" id="loading">Opening embedded model…</div><div class="unit-label">TRUE METRES · Y UP · AUTHORED VISUAL MOTION</div><div class="stats"><strong id="mesh-count">— MESH PARTS</strong><small id="triangles">— TRIANGLES</small></div><div class="cameras"><button data-camera="hero">Hero</button><button data-camera="side">Side</button><button data-camera="top">Top</button><button id="fit-current">Fit current</button><button id="fit-motion">Fit motion</button></div><div class="hint">Drag to orbit · Scroll to zoom · Right drag to pan</div></div>
<div class="toolbar"><button id="actuate" class="primary">▶ Actuate everything</button><button id="pause">Pause</button><button id="reverse">Reverse</button><button id="reset">Reset</button><div class="mode-buttons"><button data-view="surface" class="selected">SURFACE</button><button data-view="wireframe">WIREFRAME</button><button data-view="xray">X-RAY</button></div></div><div class="status" id="status" role="status">Loading current component</div></section>
<aside class="aside"><span class="eyebrow">EXPORTED MECHANISMS</span><h2>Controls</h2><p class="intro">Inspect this reusable system independently of the aircraft.</p><label class="basket-label" id="basket-label" hidden>Basket configuration<select id="basket"><option value="HIGH">High-speed visual basket</option><option value="LOW">Low-speed visual basket</option></select><small>Changing the basket returns the mechanism to rest.</small></label><div id="controls"></div><button id="cycle" class="cycle-button" hidden>Play visual cycle</button><p class="note">Animation paths and timing are authored game presentation. Reference fit and native Unreal acceptance remain open.</p><details><summary>Component evidence</summary><p id="evidence-notes"></p><div id="references"></div><p>Embedded model SHA-256</p><code id="model-hash"></code><p>Materials and animation are embedded. No parent aircraft or network download is required.</p></details></aside></main>
<footer><span>claude-design / independent component inspector</span><span>r0004 · photo-guided visual review</span></footer><script type="application/json" id="component-data">__DATA__</script><script type="module">__APP__</script></body></html>'''

APP=r'''
import * as THREE from 'three';
import {GLTFLoader} from 'gltf-loader';
import {OrbitControls} from 'orbit-controls';
import {PresentationController} from 'c130-controller';
import {PoseDriver} from 'c130-pose-driver';
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
const bundle=JSON.parse($('#component-data').textContent),art=bundle.articulation;
const stage=$('#stage'),canvas=$('#scene');
let controller,driver,model,renderer,materials=[],basketRoots=[],motionBounds,motionFitted=false,cameraKind='hero';
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(38,1,.015,1000);
const orbit=new OrbitControls(camera,canvas);orbit.enableDamping=true;orbit.dampingFactor=.075;
scene.add(new THREE.HemisphereLight(0xcce9fa,0x33413e,2.3));
for(const [color,power,position] of [[0xffecd5,4.0,[-12,18,-10]],[0xa4d6ff,2.0,[15,10,8]],[0xd0fff0,1.8,[-3,7,18]]]){const light=new THREE.DirectionalLight(color,power);light.position.set(...position);scene.add(light);}
const grid=new THREE.GridHelper(40,40,0x436a72,0x203d4b);grid.material.transparent=true;grid.material.opacity=.3;scene.add(grid);
const materialState=m=>({wireframe:m.wireframe,transparent:m.transparent,opacity:m.opacity,depthWrite:m.depthWrite,color:m.color.clone()});
function fail(message){$('#loading').hidden=false;$('#loading').classList.add('error');$('#loading').textContent=message;$('#status').textContent='Component could not be opened';}
function fitBounds(bounds){
  const center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3()),radius=Math.max(size.length()*.5,.18),angle=Math.min(THREE.MathUtils.degToRad(camera.fov)*.5,Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov)*.5)*camera.aspect));
  const distance=radius/Math.sin(angle)*1.12;
  const direction=cameraKind==='side'?new THREE.Vector3(-1,.12,.02):cameraKind==='top'?new THREE.Vector3(.001,1,.001):new THREE.Vector3(-1,.62,1.08);
  camera.position.copy(center).add(direction.normalize().multiplyScalar(distance));camera.near=Math.max(.005,distance/2000);camera.far=Math.max(400,distance*20);camera.updateProjectionMatrix();orbit.target.copy(center);orbit.minDistance=.06;orbit.maxDistance=Math.max(distance*4,100);orbit.update();
}
function boundsNow(){
  model.updateMatrixWorld(true);const bounds=new THREE.Box3(),v=new THREE.Vector3();
  model.traverseVisible(node=>{if(!node.isMesh||Math.abs(node.matrixWorld.determinant())<1e-12)return;const count=node.geometry.attributes.position.count;for(let i=0;i<count;i++){node.getVertexPosition(i,v);bounds.expandByPoint(v.applyMatrix4(node.matrixWorld));}});
  if(bounds.isEmpty())bounds.set(new THREE.Vector3(-1,-1,-1),new THREE.Vector3(1,1,1));return bounds;
}
function captureMotionBounds(){
  const current=controller.snapshot(),result=new THREE.Box3();
  for(const value of [0,.1,.25,.5,.75,1]){const sample=controller.snapshot();sample.values={};sample.phases={};for(const c of art.controls){if(c.kind==='continuous')sample.phases[c.id]=value;else sample.values[c.id]=value;}driver.apply(sample);result.union(boundsNow());}
  driver.apply(current);motionBounds=result;grid.position.y=result.min.y-.13;const extent=Math.max(10,result.getSize(new THREE.Vector3()).length()*1.7);grid.scale.setScalar(extent/40);return result;
}
function fitMotion(){fitBounds(motionBounds||captureMotionBounds());motionFitted=true;}
function fitCurrent(){fitBounds(boundsNow());motionFitted=false;}
function updateStats(){let meshes=0,triangles=0;model.traverseVisible(n=>{if(n.isMesh){meshes++;triangles+=(n.geometry.index?.count||n.geometry.attributes.position.count)/3;}});$('#mesh-count').textContent=meshes+' MESH PARTS / ARTICULATED';$('#triangles').textContent=Math.round(triangles).toLocaleString()+' TRIANGLES';}
function updateUI(snapshot){$('#status').textContent=snapshot.message;$('#pause').textContent=snapshot.paused?'Resume':'Pause';for(const c of art.controls){const input=$('#control-'+c.id),output=$('#output-'+c.id);if(input&&document.activeElement!==input)input.value=snapshot.values[c.id]||0;if(output)output.textContent=Math.round((snapshot.values[c.id]||0)*100)+'%';}}
function setView(mode){for(const {material,original} of materials){material.wireframe=mode==='wireframe';material.transparent=mode==='xray'?true:original.transparent;material.opacity=mode==='xray'?.22:original.opacity;material.depthWrite=mode==='xray'?false:original.depthWrite;material.color.copy(original.color);if(mode==='wireframe')material.color.setHex(0x9ee8d9);material.needsUpdate=true;}for(const button of $$('[data-view]'))button.classList.toggle('selected',button.dataset.view===mode);}
function switchBasket(kind){controller.reset();driver.apply(controller.snapshot());for(const root of basketRoots)root.visible=root.name.endsWith('_'+kind);captureMotionBounds();updateStats();fitCurrent();updateUI(controller.snapshot());}
async function start(){
  try{
    renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.18;
    const resize=()=>{const {width,height}=stage.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();};new ResizeObserver(resize).observe(stage);resize();
    const packed=Uint8Array.from(atob(bundle.glb),c=>c.charCodeAt(0));if(!globalThis.DecompressionStream)throw new Error('Use a browser that supports gzip DecompressionStream.');
    const buffer=await new Response(new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    if(globalThis.crypto?.subtle){const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer)),v=>v.toString(16).padStart(2,'0')).join('');if(digest!==bundle.sha256||digest!==art.sha256)throw new Error('Embedded model checksum mismatch.');}
    const loaded=await new Promise((resolve,reject)=>new GLTFLoader().parse(buffer,'',resolve,reject));model=loaded.scene;scene.add(model);
    model.traverse(n=>{if(n.userData.loadout_module_root){const enabled=n.userData.default_enabled??n.scale.toArray().some(v=>v!==0);n.scale.fromArray(n.userData.canonical_scale||[1,1,1]);n.visible=enabled;if(/_BASKET_(HIGH|LOW)$/.test(n.name))basketRoots.push(n);}});
    controller=new PresentationController(art);driver=new PoseDriver(model,loaded.animations,art);if(driver.missing.length)throw new Error('Missing animation bindings: '+JSON.stringify(driver.missing));
    model.traverse(n=>{if(n.isMesh){const source=Array.isArray(n.material)?n.material:[n.material],copies=source.map(m=>m.clone());n.material=copies.length===1?copies[0]:copies;for(const m of copies)materials.push({material:m,original:materialState(m)});}});
    if(basketRoots.some(n=>n.name.endsWith('_HIGH'))&&basketRoots.some(n=>n.name.endsWith('_LOW')))$('#basket-label').hidden=false;
    const list=$('#controls');for(const c of art.controls){const row=document.createElement('div');row.className='control';const label=document.createElement('label');label.htmlFor='control-'+c.id;label.textContent=c.label;const output=document.createElement('output');output.id='output-'+c.id;output.textContent='0%';label.append(output);const input=document.createElement('input');input.type='range';input.id='control-'+c.id;input.min=0;input.max=1;input.step=.001;input.value=0;input.setAttribute('aria-label',c.label);input.addEventListener('input',()=>{if(!motionFitted)fitMotion();controller.set(c.id,+input.value);});const endpoints=document.createElement('div');endpoints.className='endpoints';const lo=document.createElement('span'),hi=document.createElement('span');lo.textContent=c.states?.rest||'Rest';hi.textContent=c.states?.deployed||'Deployed';endpoints.append(lo,hi);row.append(label,input,endpoints);list.append(row);}
    const cycles=art.controls.filter(c=>c.kind==='cycle');if(cycles.length){$('#cycle').hidden=false;$('#cycle').addEventListener('click',()=>{fitMotion();controller.fire(cycles[0].id,1);});}
    const references=[...new Set(art.controls.flatMap(c=>c.evidence?.sources||[]))];$('#evidence-notes').textContent=[...new Set(art.controls.map(c=>c.evidence?.limitations).filter(Boolean))].join(' ');for(const url of references){const p=document.createElement('p');p.className='evidence-link';const a=document.createElement('a');a.href=url;a.textContent=url;a.target='_blank';a.rel='noopener';p.append(a);$('#references').append(p);}$('#model-hash').textContent=bundle.sha256;
    driver.apply(controller.snapshot());captureMotionBounds();fitCurrent();updateStats();$('#loading').hidden=true;updateUI(controller.snapshot());
    $('#actuate').addEventListener('click',()=>{fitMotion();controller.actuateEverything();});$('#pause').addEventListener('click',()=>controller.togglePause());$('#reverse').addEventListener('click',()=>controller.reverse());$('#reset').addEventListener('click',()=>{controller.reset();driver.apply(controller.snapshot());updateUI(controller.snapshot());});$('#fit-current').addEventListener('click',fitCurrent);$('#fit-motion').addEventListener('click',fitMotion);$('#basket').addEventListener('change',e=>switchBasket(e.target.value));
    for(const button of $$('[data-camera]'))button.addEventListener('click',()=>{cameraKind=button.dataset.camera;for(const b of $$('[data-camera]'))b.classList.toggle('selected',b===button);if(motionFitted)fitMotion();else fitCurrent();});for(const button of $$('[data-view]'))button.addEventListener('click',()=>setView(button.dataset.view));
    window.JCNC_COMPONENT_REVIEW={id:bundle.id,sha256:bundle.sha256,articulation:art,scene:model,controller,driver,switchBasket,fitMotion,fitCurrent};
    let previous=performance.now(),frame=0;const render=now=>{const dt=Math.min((now-previous)/1000,.1);previous=now;const snapshot=controller.tick(dt);driver.apply(snapshot);if(frame++%3===0)updateUI(snapshot);orbit.update();renderer.render(scene,camera);requestAnimationFrame(render);};requestAnimationFrame(render);
  }catch(error){console.error(error);fail(error.message);}
}
start();
'''

NODE_QA=r'''
import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';import {gunzipSync} from 'node:zlib';import vm from 'node:vm';
import {GLTFLoader} from 'gltf-loader';import {PresentationController} from 'c130-controller';import {PoseDriver} from 'c130-pose-driver';
const bundle=JSON.parse(fs.readFileSync(new URL('./bundle.json',import.meta.url),'utf8')),modules=JSON.parse(fs.readFileSync(new URL('./module-index.json',import.meta.url),'utf8'));
for(const [name,file]of Object.entries(modules)){const module=new vm.SourceTextModule(fs.readFileSync(new URL(file,import.meta.url),'utf8'),{identifier:name});for(const spec of module.dependencySpecifiers)assert(spec in modules,'Unbundled dependency '+spec);}
const app=new vm.SourceTextModule(fs.readFileSync(new URL('./app.mjs',import.meta.url),'utf8'),{identifier:'app'});for(const spec of app.dependencySpecifiers)assert(spec in modules,'Unbundled application dependency '+spec);
globalThis.self=globalThis;globalThis.createImageBitmap=async()=>({width:1,height:1,close(){}});globalThis.ProgressEvent=class extends Event{constructor(t,p={}){super(t);Object.assign(this,p);}};
const originalFetch=globalThis.fetch;let externalRequests=0;globalThis.fetch=(input,options)=>{const url=typeof input==='string'?input:input?.url||String(input);if(!/^(blob:|data:)/.test(url)){externalRequests++;throw new Error('External request attempted in isolated inspector test: '+url);}return originalFetch(input,options);};
const bytes=gunzipSync(Buffer.from(bundle.glb,'base64'));const digest=crypto.createHash('sha256').update(bytes).digest('hex');assert.equal(digest,bundle.sha256);assert.equal(digest,bundle.articulation.sha256);
const doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString('utf8'));for(const resource of [...(doc.images||[]),...(doc.buffers||[])])assert(!resource.uri||resource.uri.startsWith('data:'),'External GLB dependency');
const gltf=await new Promise((ok,bad)=>new GLTFLoader().parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'',ok,bad));
const roots=[];gltf.scene.traverse(n=>{if(n.userData.loadout_module_root){const enabled=n.userData.default_enabled??n.scale.toArray().some(v=>v!==0);n.scale.fromArray(n.userData.canonical_scale||[1,1,1]);n.visible=enabled;roots.push(n);}});
const controller=new PresentationController(bundle.articulation),driver=new PoseDriver(gltf.scene,gltf.animations,bundle.articulation);assert.equal(driver.missing.length,0,JSON.stringify(driver.missing));
const rests=new Map();gltf.scene.traverse(n=>rests.set(n.uuid,{n,p:n.position.toArray(),q:n.quaternion.toArray(),s:n.scale.toArray(),m:n.morphTargetInfluences?Array.from(n.morphTargetInfluences):null}));
let maximumResetError=0;const checkRest=()=>{for(const r of rests.values()){for(const [now,before]of [[r.n.position.toArray(),r.p],[r.n.quaternion.toArray(),r.q],[r.n.scale.toArray(),r.s]])for(let i=0;i<now.length;i++){maximumResetError=Math.max(maximumResetError,Math.abs(now[i]-before[i]));assert(Math.abs(now[i]-before[i])<1e-6,'Transform did not reset '+r.n.name);}if(r.m)assert.deepEqual(r.n.morphTargetInfluences,r.m,'Morph did not reset '+r.n.name);}};
const deltas={};for(const c of bundle.articulation.controls){let delta=0;for(const phase of [.1,.25,.5,.75,1]){const snap=controller.snapshot();snap.values={};snap.phases={};snap[c.kind==='continuous'?'phases':'values'][c.id]=phase;driver.apply(snap);for(const r of rests.values()){for(const [now,before]of [[r.n.position.toArray(),r.p],[r.n.quaternion.toArray(),r.q],[r.n.scale.toArray(),r.s]])for(let i=0;i<now.length;i++)delta=Math.max(delta,Math.abs(now[i]-before[i]));if(r.m)for(let i=0;i<r.m.length;i++)delta=Math.max(delta,Math.abs(r.n.morphTargetInfluences[i]-r.m[i]));}}assert(delta>1e-5,'Control did not move actual model '+c.id);deltas[c.id]=delta;}
controller.reset();controller.actuateEverything();for(let i=0;i<1500;i++)driver.apply(controller.tick(1/60));assert.equal(controller.covered.size,controller.controls.length,'Missing global control coverage');controller.togglePause();const snapshot=controller.snapshot();for(let i=0;i<10;i++)driver.apply(controller.tick(.1));assert.deepEqual(controller.snapshot(),snapshot,'Pause drift');controller.reverse();for(let i=0;i<1500;i++)driver.apply(controller.tick(1/60));controller.reset();driver.apply(controller.snapshot());checkRest();
const baskets=roots.filter(n=>/_BASKET_(HIGH|LOW)$/.test(n.name));for(const kind of ['HIGH','LOW'])if(baskets.length){for(const n of baskets)n.visible=n.name.endsWith('_'+kind);controller.actuateEverything();for(let i=0;i<750;i++)driver.apply(controller.tick(1/60));controller.reset();driver.apply(controller.snapshot());checkRest();assert(baskets.filter(n=>n.visible).length===1,'Basket configuration overlap');}
assert.equal(externalRequests,0);console.log(JSON.stringify({status:'PASS',component:bundle.id,model_sha256:digest,controls:controller.controls.length,clips:gltf.animations.length,control_transform_or_morph_deltas:deltas,global_coverage:'PASS',pause:'PASS',reverse:'PASS',reset:'PASS',basket_selection:baskets.length?'HIGH_AND_LOW_CHECKED':'NOT_APPLICABLE',reset_max_transform_error:maximumResetError,embedded_module_parse:'PASS',dependency_closure:'PASS',external_network_requests:externalRequests,remote_fetch_blocked_during_test:true,scope:'Isolated component bytes and embedded runtime extracted from the generated HTML; CPU Three.js loading/animation only with texture decoding stubbed. Browser/WebGL, photographic fit, physical clearance and Unreal NOT_RUN.'}));
'''

def parse_payload(text):
    return json.loads(re.search(r'<script type="application/json" id="component-data">([\s\S]*?)</script>',text).group(1))

def verify_inspector(text,model_bytes):
    payload=parse_payload(text)
    assert gzip.decompress(base64.b64decode(payload['glb']))==model_bytes
    imports=json.loads(re.search(r'<script type="importmap">([\s\S]*?)</script>',text).group(1))['imports']
    app=re.search(r'<script type="module">([\s\S]*?)</script>',text).group(1)
    with tempfile.TemporaryDirectory(prefix='claude-design-component-inspector-') as directory:
        root=Path(directory);mapping={}
        for key,url in imports.items():
            assert url.startswith('data:text/javascript;base64,')
            source=base64.b64decode(url.split(',',1)[1]).decode()
            filename=key+'.mjs';(root/filename).write_text(source);mapping[key]='./'+filename
        (root/'module-index.json').write_text(json.dumps(mapping))
        (root/'bundle.json').write_text(json.dumps(payload))
        (root/'app.mjs').write_text(app)
        (root/'test.mjs').write_text(NODE_QA)
        (root/'loader.mjs').write_text("const modules="+json.dumps(mapping)+";export async function resolve(specifier,context,next){if(specifier in modules)return {url:new URL(modules[specifier],import.meta.url).href,shortCircuit:true};return next(specifier,context);}\n")
        command=['node','--experimental-vm-modules','--loader',str(root/'loader.mjs'),str(root/'test.mjs')]
        result=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=90)
        if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
        return json.loads(result.stdout.strip().splitlines()[-1])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only',choices=list(COMPONENTS));args=parser.parse_args()
    imports={};module_hashes={}
    for key,relative in MODULES.items():
        source=(HERE/relative).read_text()
        if key=='gltf-loader':source=source.replace("'./BufferGeometryUtils.js'","'c130-buffer-utils'")
        imports[key]='data:text/javascript;base64,'+base64.b64encode(source.encode()).decode();module_hashes[key]=sha(source.encode())
    for key,title in COMPONENTS.items():
        if args.only and args.only!=key:continue
        directory=REV/'components'/key
        data=(directory/'model.glb').read_bytes();art_bytes=(directory/'articulation.json').read_bytes();art=json.loads(art_bytes)
        assert sha(data)==art['sha256'],'Component model/articulation mismatch '+key
        payload={'id':key,'title':title,'revision':'r0004','sha256':sha(data),'glb':base64.b64encode(gzip.compress(data,compresslevel=9,mtime=0)).decode(),'encoding':'gzip+base64','articulation':art}
        text=TEMPLATE.replace('__TITLE__',html.escape(title)).replace('__STYLE__',STYLE).replace('__IMPORTMAP__',json.dumps({'imports':imports},separators=(',',':'))).replace('__DATA__',json.dumps(payload,separators=(',',':')).replace('</','<\\/')).replace('__APP__',APP.replace('</script','<\\/script'))
        qa=verify_inspector(text,data)
        path=directory/'inspector.html';path.write_text(text)
        manifest={'author':'claude-design','revision':'r0004','component_id':key,'file':'inspector.html','bytes':path.stat().st_size,'sha256':sha(path.read_bytes()),'model_file':'model.glb','model_sha256':sha(data),'articulation_sha256':sha(art_bytes),'source_module_hashes':module_hashes,'parent_aircraft_dependency':False,'external_network_dependency':False,'standalone_articulation':True,'runtime':'Three.js 0.170.0; browser WebGL2 and gzip DecompressionStream','controls':['Actuate everything','Pause','Reverse','Reset','Individual exported controls','Surface / wireframe / X-ray','Fit current / fit motion'],'basket_selector':'HIGH_LOW' if key.startswith('hose-drogue') else 'NOT_APPLICABLE','verification':qa,'browser_rendering':'NOT_RUN','native_unreal':'NOT_RUN'}
        (directory/'inspector.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print('claude-design '+json.dumps({'component':key,'inspector_bytes':manifest['bytes'],'inspector_sha256':manifest['sha256'],'model_sha256':manifest['model_sha256'],'isolated_runtime':qa['status'],'reset_error':qa['reset_max_transform_error']}),flush=True)
if __name__=='__main__':main()
