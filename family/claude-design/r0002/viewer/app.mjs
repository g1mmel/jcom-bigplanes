/** claude-design | C-130 family viewer. Uses exported model clips and adjacent articulation. */
import * as THREE from 'three';
import { GLTFLoader } from 'gltf-loader';
import { OrbitControls } from 'orbit-controls';
import { PresentationController } from 'c130-controller';
import { PoseDriver } from 'c130-pose-driver';

const $=s=>document.querySelector(s);
const $$=s=>Array.from(document.querySelectorAll(s));
const canvas=$('#scene'), panel=$('#canvas-panel');
const bundleElement=$('#embedded-assets');
const bundle=bundleElement?JSON.parse(bundleElement.textContent):null;
if(bundle?.notes){$('#notes-link').addEventListener('click',e=>{e.preventDefault();const target=$('#notes-text');target.replaceChildren();for(const part of bundle.notes.split(/(https?:\/\/[^\s)\]>]+)/g)){if(/^https?:\/\//.test(part)){const a=document.createElement('a');a.href=part;a.textContent=part;a.target='_blank';a.rel='noopener';target.append(a);}else target.append(document.createTextNode(part));}$('#notes-dialog').showModal();});}
if(bundle){const link=$('.validation a');link.textContent='Embedded model inventory ↗';link.addEventListener('click',e=>{e.preventDefault();$('#notes-text').textContent=JSON.stringify({revision:bundle.revision,models:Object.fromEntries(Object.entries(bundle.models).map(([id,item])=>[id,{sha256:item.sha256,controls:item.articulation.controls.length,acceptance:item.articulation.acceptance}]))},null,2);$('#notes-dialog').showModal();});}
const catalog={
  c130:{name:'C-130H HERCULES',label:'C-130H · Hercules'},
  ac130:{name:'AC-130W STINGER II',label:'AC-130W · Stinger II (circa 2021)'},
  ac130j:{name:'AC-130J GHOSTRIDER',label:'AC-130J · Ghostrider candidate'}
};
let renderer;
try { renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:'high-performance'}); }
catch(e){showError('WebGL could not start. '+e.message);throw e;}
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.25; renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(36,1,.05,800);
camera.position.set(-48,25,-43);
const orbit=new OrbitControls(camera,canvas); orbit.enableDamping=true;orbit.dampingFactor=.07;
orbit.minDistance=2;orbit.maxDistance=180;orbit.maxPolarAngle=Math.PI*.98;orbit.target.set(0,4,0);
scene.add(new THREE.HemisphereLight(0xc6e8ff,0x344044,2.1));
const key=new THREE.DirectionalLight(0xfff2db,3.8);key.position.set(-35,55,-35);key.castShadow=true;
key.shadow.mapSize.set(2048,2048);key.shadow.camera.left=-30;key.shadow.camera.right=30;key.shadow.camera.top=30;key.shadow.camera.bottom=-30;key.shadow.camera.far=130;key.shadow.normalBias=.06;scene.add(key);
const fill=new THREE.DirectionalLight(0x9dc7f1,1.8);fill.position.set(35,20,10);scene.add(fill);
const rim=new THREE.DirectionalLight(0xddf9ff,1.7);rim.position.set(-20,10,40);scene.add(rim);
const grid=new THREE.GridHelper(120,60,0x436476,0x203c4c);grid.position.y=-.035;grid.material.transparent=true;grid.material.opacity=.45;scene.add(grid);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(150,150),new THREE.ShadowMaterial({color:0x00060a,opacity:.3}));ground.rotation.x=-Math.PI/2;ground.position.y=-.025;ground.receiveShadow=true;scene.add(ground);
const assetRoot=new THREE.Group();scene.add(assetRoot);
let loaded=null, controller=null, driver=null, articulation=null, activeId=null, view='surface', materials=[], modelBounds=null, loadToken=0, frameId=0, lastTime=performance.now(), cameraTween=null;

function resize(){const {width,height}=panel.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(panel);resize();
function showError(message){$('#load-detail').textContent=message;$('#error-message').textContent=message;$('#error-dialog').showModal();}
function decode64(s){const b=atob(s),a=new Uint8Array(b.length);for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return a.buffer;}
async function getInput(id){
  if(bundle){const item=bundle.models[id];if(!item)throw new Error('Portable model missing: '+id);let buffer=decode64(item.glb);if(item.encoding==='gzip+base64'){if(!globalThis.DecompressionStream)throw new Error('Use a current browser with gzip DecompressionStream, or open the folder viewer through its local server.');buffer=await new Response(new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();}return {buffer,art:item.articulation};}
  const [m,a]=await Promise.all([fetch('../models/'+id+'.glb'),fetch('../articulation/'+id+'.json')]);
  if(!m.ok)throw new Error('GLB request failed: '+m.status);if(!a.ok)throw new Error('Articulation request failed: '+a.status);
  return {buffer:await m.arrayBuffer(),art:await a.json()};
}
function disposeModel(){
  if(!loaded)return;
  loaded.scene.traverse(n=>{if(n.geometry)n.geometry.dispose();if(n.material){for(const m of Array.isArray(n.material)?n.material:[n.material]){for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}}});
  assetRoot.remove(loaded.scene);loaded=null;materials=[];
}
async function loadAsset(id){
  const token=++loadToken;$('#loading').classList.remove('hidden');$('#load-detail').textContent='Reading GLB and mechanism data';
  for(const b of $$('.transport button'))b.disabled=true;
  try{
    const input=await getInput(id);const loader=new GLTFLoader();
    if(input.art.sha256&&globalThis.crypto?.subtle){$('#load-detail').textContent='Verifying model checksum';const digest=await crypto.subtle.digest('SHA-256',input.buffer);const actual=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');if(actual!==input.art.sha256)throw new Error('Model checksum does not match its articulation revision.');}
    const gltf=await new Promise((resolve,reject)=>loader.parse(input.buffer,'',resolve,reject));
    if(token!==loadToken)return;
    disposeModel(); loaded=gltf;articulation=input.art;activeId=id;
    assetRoot.add(gltf.scene);controller=new PresentationController(articulation);driver=new PoseDriver(gltf.scene,gltf.animations,articulation);
    let meshCount=0,triangles=0;const meshes=[];
    gltf.scene.traverse(n=>{if(n.isMesh){meshCount++;triangles+=(n.geometry.index?.count||n.geometry.attributes.position.count)/3;meshes.push(n);n.castShadow=true;n.receiveShadow=true;}});
    for(const n of meshes){
      const mats=Array.isArray(n.material)?n.material:[n.material];
      n.material=mats.map(m=>m.clone());if(!Array.isArray(n.userData.originalMaterialArray)&&mats.length===1)n.material=n.material[0];
      const current=Array.isArray(n.material)?n.material:[n.material];
      for(const m of current)materials.push({m,original:{transparent:m.transparent,opacity:m.opacity,depthWrite:m.depthWrite,wireframe:m.wireframe||false,side:m.side,colorWrite:m.colorWrite,polygonOffset:m.polygonOffset,polygonOffsetFactor:m.polygonOffsetFactor,polygonOffsetUnits:m.polygonOffsetUnits}});
      const lines=new THREE.LineSegments(new THREE.EdgesGeometry(n.geometry,26),new THREE.LineBasicMaterial({color:0x8cdbc9,transparent:true,opacity:.62,depthTest:true}));
      lines.name='QA_EDGES_'+n.name;lines.visible=false;lines.userData.qaEdges=true; n.add(lines);n.userData.qaEdges=lines;
      const topology=new THREE.LineSegments(new THREE.WireframeGeometry(n.geometry),new THREE.LineBasicMaterial({color:0x9bdacb,transparent:true,opacity:.64,depthTest:true}));
      topology.name='QA_TOPOLOGY_'+n.name;topology.visible=false;topology.renderOrder=1;n.add(topology);n.userData.qaTopology=topology;
    }
    modelBounds=new THREE.Box3().setFromObject(gltf.scene);ground.position.y=modelBounds.min.y-.035;grid.position.y=modelBounds.min.y-.04;
    $('#model-designation').textContent=articulation.designation||(articulation.label?articulation.label.split(' — ')[0].replace(/ candidate$/,''):catalog[id].name);
    const option=$('#asset').querySelector('option[value="'+id+'"]');if(option&&articulation.label)option.textContent=articulation.label;
    $('#mesh-count').textContent=meshCount+' MESH PARTS / ARTICULATED';
    $('#triangle-count').textContent=Math.round(triangles).toLocaleString()+' TRIANGLES';
    $('#control-count').textContent=articulation.controls.length;
    $('#loaded-file').textContent=id+'.glb';$('#clip-count').textContent=gltf.animations.length;
    $('#binding-status').textContent=driver.missing.length?driver.missing.length+' unresolved bindings':'All exported controls bound';
    if(driver.missing.length)throw new Error('Unresolved animation bindings: '+JSON.stringify(driver.missing));
    rebuildControls();applyView(view);selectPresetButton('PARKED');cameraView('hero',false);
    $('#loading').classList.add('hidden');for(const b of $$('.transport button'))b.disabled=false;
    $('#asset').value=id;window.C130_REVIEW={model:id,revision:articulation.revision,meshCount,triangles,clips:gltf.animations.length,bindings:driver.missing,controller,driver,scene:gltf.scene};
    dispatchEvent(new CustomEvent('c130:model-loaded',{detail:{id,meshCount,triangles,clips:gltf.animations.length}}));
  }catch(e){console.error(e);showError(e.message);}
}
function rebuildControls(){
  const list=$('#mechanism-list');list.replaceChildren();const groups=new Map();
  for(const c of articulation.controls){const key=c.group||'Mechanisms';if(!groups.has(key))groups.set(key,[]);groups.get(key).push(c);}
  for(const [name,items]of groups){
    const group=document.createElement('section');group.className='mechanism-group';
    const title=document.createElement('div');title.className='group-title';title.textContent=name.replaceAll('_',' ');const count=document.createElement('span');count.textContent=items.length;title.append(count);group.append(title);
    for(const c of items){
      const row=document.createElement('div');row.className='mechanism';row.dataset.control=c.id;row.dataset.search=(c.id+' '+c.label+' '+name).toLowerCase();
      const top=document.createElement('div');top.className='mechanism-top';const label=document.createElement('label');label.htmlFor='ctl-'+c.id;label.textContent=c.label||c.id;const out=document.createElement('output');out.id='out-'+c.id;out.textContent='0%';top.append(label,out);
      const input=document.createElement('input');input.type='range';input.id='ctl-'+c.id;input.min=0;input.max=1;input.step=.001;input.value=0;input.setAttribute('aria-label',c.label||c.id);input.addEventListener('input',()=>{controller.set(c.id,+input.value);selectPresetButton(null);});
      const endpoints=document.createElement('small');const lo=document.createElement('span'),hi=document.createElement('span');lo.textContent=c.states?.rest||'Rest';hi.textContent=c.kind==='continuous'?'Running':c.states?.deployed||'Deployed';endpoints.append(lo,hi);
      const reason=document.createElement('div');reason.className='block-reason';row.append(top,input,endpoints,reason);group.append(row);
    }
    list.append(group);
  }
  filterControls();
}
function filterControls(){const term=$('#filter').value.toLowerCase();for(const row of $$('.mechanism'))row.hidden=!row.dataset.search.includes(term);for(const g of $$('.mechanism-group'))g.hidden=!Array.from(g.querySelectorAll('.mechanism')).some(r=>!r.hidden);}
function selectPresetButton(mode){for(const b of $$('[data-preset]'))b.classList.toggle('selected',b.dataset.preset===mode);}
function applyView(mode){view=mode;for(const r of materials){const m=r.m,o=r.original;m.wireframe=false;m.transparent=o.transparent;m.opacity=o.opacity;m.depthWrite=o.depthWrite;m.side=o.side;m.colorWrite=o.colorWrite;m.polygonOffset=o.polygonOffset;m.polygonOffsetFactor=o.polygonOffsetFactor;m.polygonOffsetUnits=o.polygonOffsetUnits;if(mode==='wireframe'){m.transparent=false;m.opacity=1;m.colorWrite=false;m.depthWrite=true;m.polygonOffset=true;m.polygonOffsetFactor=1;m.polygonOffsetUnits=1;}if(mode==='xray'){m.transparent=true;m.opacity=.14;m.depthWrite=false;m.side=THREE.DoubleSide;}m.needsUpdate=true;}loaded?.scene.traverse(n=>{if(n.userData.qaEdges?.isObject3D)n.userData.qaEdges.visible=mode==='xray';if(n.userData.qaTopology?.isObject3D)n.userData.qaTopology.visible=mode==='wireframe';});for(const b of $$('[data-view]'))b.classList.toggle('selected',b.dataset.view===mode);ground.visible=mode==='surface';}
function cameraView(name,animate=true){
  const center=modelBounds?modelBounds.getCenter(new THREE.Vector3()):new THREE.Vector3(0,5,0);
  const poses={hero:{p:[-47,26,-43],t:[0,5,0]},side:{p:[-66,8,0],t:[0,5,0]},front:{p:[0,9,-66],t:[0,5,-1]},top:{p:[0,77,.01],t:[0,0,0]},doors:{p:[-15,8,-15],t:[-1.2,3.5,-8]},ramp:{p:[-14,8,28],t:[0,3.2,10]}};
  const pose=poses[name]||poses.hero;const p=new THREE.Vector3(...pose.p),t=new THREE.Vector3(...pose.t);
  if(animate)cameraTween={from:camera.position.clone(),to:p,targetFrom:orbit.target.clone(),targetTo:t,start:performance.now(),duration:650};else{camera.position.copy(p);orbit.target.copy(t);orbit.update();}
  for(const b of $$('[data-camera]'))b.classList.toggle('selected',b.dataset.camera===name);
}
function updateUI(snapshot){
  $('#transport-status').textContent=snapshot.message;$('#pause').textContent=snapshot.paused?'Resume':'Pause';$('#direction-icon').textContent=snapshot.paused?'Ⅱ':snapshot.direction<0?'◀':snapshot.running?'▶':'●';
  $('#global-progress').style.width=(snapshot.globalTime*100)+'%';
  for(const c of articulation.controls){const row=$('[data-control="'+c.id+'"]'),input=$('#ctl-'+c.id),out=$('#out-'+c.id);if(!row)continue;const v=snapshot.values[c.id]||0;if(document.activeElement!==input)input.value=v;out.textContent=Math.round(v*100)+'%';const blocked=snapshot.blocked[c.id];row.classList.toggle('blocked',!!blocked);row.querySelector('.block-reason').textContent=blocked||'';}
}
$('#asset').addEventListener('change',e=>loadAsset(e.target.value));$('#filter').addEventListener('input',filterControls);
for(const b of $$('[data-camera]'))b.addEventListener('click',()=>cameraView(b.dataset.camera));
for(const b of $$('[data-view]'))b.addEventListener('click',()=>applyView(b.dataset.view));
for(const b of $$('[data-preset]'))b.addEventListener('click',()=>{controller?.preset(b.dataset.preset);selectPresetButton(b.dataset.preset);});
$('#actuate').addEventListener('click',()=>{controller?.actuateEverything();selectPresetButton(null);});$('#pause').addEventListener('click',()=>controller?.togglePause());$('#reverse').addEventListener('click',()=>controller?.reverse());$('#reset').addEventListener('click',()=>{controller?.reset();selectPresetButton('PARKED');});
$('#default').addEventListener('click',()=>{controller?.reset();selectPresetButton('PARKED');applyView('surface');cameraView('hero');});
orbit.addEventListener('start',()=>{cameraTween=null;for(const b of $$('[data-camera]'))b.classList.remove('selected');});
function frame(now){
  const dt=Math.min((now-lastTime)/1000,.1);lastTime=now;
  if(controller&&driver){const state=controller.tick(dt);driver.apply(state);if(frameId%3===0)updateUI(state);}
  if(cameraTween){const raw=Math.min((now-cameraTween.start)/cameraTween.duration,1),t=raw*raw*(3-2*raw);camera.position.lerpVectors(cameraTween.from,cameraTween.to,t);orbit.target.lerpVectors(cameraTween.targetFrom,cameraTween.targetTo,t);if(raw===1)cameraTween=null;}
  orbit.update();renderer.render(scene,camera);frameId++;requestAnimationFrame(frame);
}
requestAnimationFrame(frame);loadAsset(new URLSearchParams(location.search).get('asset') in catalog?new URLSearchParams(location.search).get('asset'):'c130');
