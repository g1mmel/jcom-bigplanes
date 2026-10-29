/** claude-design | C-130 family viewer. Uses exported model clips and adjacent articulation. */
import * as THREE from 'three';
import { GLTFLoader } from 'gltf-loader';
import { OrbitControls } from 'orbit-controls';
import { PresentationController } from 'c130-controller';
import { PoseDriver } from 'c130-pose-driver';
import { LoadoutManager, visibleMeshStats, normalizeModuleScales } from 'c130-loadouts';

const $=s=>document.querySelector(s);
const $$=s=>Array.from(document.querySelectorAll(s));
const canvas=$('#scene'), panel=$('#canvas-panel');
const bundleElement=$('#embedded-assets');
const bundle=bundleElement?JSON.parse(bundleElement.textContent):null;
if(bundle?.notes){$('#notes-link').addEventListener('click',e=>{e.preventDefault();const target=$('#notes-text');target.replaceChildren();for(const part of bundle.notes.split(/(https?:\/\/[^\s)\]>]+)/g)){if(/^https?:\/\//.test(part)){const a=document.createElement('a');a.href=part;a.textContent=part;a.target='_blank';a.rel='noopener';target.append(a);}else target.append(document.createTextNode(part));}$('#notes-dialog').showModal();});}
if(bundle){const link=$('.validation a');link.textContent='Embedded model inventory ↗';link.addEventListener('click',e=>{e.preventDefault();$('#notes-text').textContent=JSON.stringify({revision:bundle.revision,models:Object.fromEntries(Object.entries(bundle.models).map(([id,item])=>[id,{sha256:item.sha256,controls:item.articulation.controls.length,acceptance:item.articulation.acceptance}]))},null,2);$('#notes-dialog').showModal();});}
const catalog={'c130-family':{name:'C-130 FAMILY',label:'C-130 · shared modular airframe'}};
if(bundle){for(const option of Array.from($('#asset').options))if(!(option.value in bundle.models))option.remove();for(const group of $$('#asset optgroup'))if(!group.children.length)group.remove();}
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
orbit.minDistance=.15;orbit.maxDistance=180;orbit.maxPolarAngle=Math.PI*.98;orbit.target.set(0,4,0);
scene.add(new THREE.HemisphereLight(0xc6e8ff,0x344044,2.1));
const key=new THREE.DirectionalLight(0xfff2db,3.8);key.position.set(-35,55,-35);key.castShadow=true;
key.shadow.mapSize.set(2048,2048);key.shadow.camera.left=-30;key.shadow.camera.right=30;key.shadow.camera.top=30;key.shadow.camera.bottom=-30;key.shadow.camera.far=130;key.shadow.normalBias=.06;scene.add(key);
const fill=new THREE.DirectionalLight(0x9dc7f1,1.8);fill.position.set(35,20,10);scene.add(fill);
const rim=new THREE.DirectionalLight(0xddf9ff,1.7);rim.position.set(-20,10,40);scene.add(rim);
const grid=new THREE.GridHelper(120,60,0x436476,0x203c4c);grid.position.y=-.035;grid.material.transparent=true;grid.material.opacity=.45;scene.add(grid);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(150,150),new THREE.ShadowMaterial({color:0x00060a,opacity:.3}));ground.rotation.x=-Math.PI/2;ground.position.y=-.025;ground.receiveShadow=true;scene.add(ground);
const assetRoot=new THREE.Group();scene.add(assetRoot);
let loaded=null, controller=null, driver=null, articulation=null, activeArticulation=null, loadouts=null, activeId=null, view='surface', materials=[], modelBounds=null, loadToken=0, frameId=0, lastTime=performance.now(), cameraTween=null;

function resize(){const {width,height}=panel.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(panel);resize();
function showError(message){$('#load-detail').textContent=message;$('#error-message').textContent=message;$('#error-dialog').showModal();}
function decode64(s){const b=atob(s),a=new Uint8Array(b.length);for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return a.buffer;}
async function getInput(id){
  if(bundle){const item=bundle.models[id];if(!item)throw new Error('Portable model missing: '+id);let buffer=decode64(item.glb);if(item.encoding==='gzip+base64'){if(!globalThis.DecompressionStream)throw new Error('Use a current browser with gzip DecompressionStream, or open the folder viewer through its local server.');buffer=await new Response(new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();}return {buffer,art:item.articulation,catalog:bundle.loadouts};}
  const [m,a,l]=await Promise.all([fetch('../models/'+id+'.glb'),fetch('../articulation/'+id+'.json'),fetch('../loadouts/catalog.json')]);
  if(!m.ok)throw new Error('GLB request failed: '+m.status);if(!a.ok)throw new Error('Articulation request failed: '+a.status);
  if(!l.ok)throw new Error('Loadout catalogue request failed: '+l.status);
  return {buffer:await m.arrayBuffer(),art:await a.json(),catalog:await l.json()};
}
function disposeSceneResources(root){root.traverse(n=>{if(n.geometry)n.geometry.dispose();if(n.material){for(const m of Array.isArray(n.material)?n.material:[n.material]){for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}}});}
function disposeModel(){
  if(!loaded)return;
  loaded.scene.traverse(n=>{if(n.geometry)n.geometry.dispose();if(n.material){for(const m of Array.isArray(n.material)?n.material:[n.material]){for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}}});
  assetRoot.remove(loaded.scene);loaded=null;materials=[];
}
async function loadAsset(id){
  const token=++loadToken;controller?.reset();if(controller&&driver)driver.apply(controller.snapshot());$('#loading').classList.remove('hidden');$('#load-detail').textContent='Reading GLB and mechanism data';
  for(const b of $$('.transport button,.firing-panel button'))b.disabled=true;
  try{
    const input=await getInput(id);const loader=new GLTFLoader();
    if(input.art.sha256&&globalThis.crypto?.subtle){$('#load-detail').textContent='Verifying model checksum';const digest=await crypto.subtle.digest('SHA-256',input.buffer);const actual=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');if(actual!==input.art.sha256)throw new Error('Model checksum does not match its articulation revision.');}
    const gltf=await new Promise((resolve,reject)=>loader.parse(input.buffer,'',resolve,reject));
    if(token!==loadToken){disposeSceneResources(gltf.scene);return;}
    disposeModel(); loaded=gltf;articulation=input.art;activeId=id;
    assetRoot.add(gltf.scene);normalizeModuleScales(gltf.scene,input.catalog);controller=new PresentationController(articulation);driver=new PoseDriver(gltf.scene,gltf.animations,articulation);
    loadouts=new LoadoutManager(input.catalog,gltf.scene,articulation);
    let meshCount=0,triangles=0;const meshes=[];
    gltf.scene.traverse(n=>{if(n.isMesh){meshCount++;triangles+=(n.geometry.index?.count||n.geometry.attributes.position.count)/3;meshes.push(n);n.castShadow=!/FLASH|SMOKE|GLOW|PLUME/.test(n.name);n.receiveShadow=true;}});
    for(const n of meshes){
      const mats=Array.isArray(n.material)?n.material:[n.material];
      n.material=mats.map(m=>m.clone());if(!Array.isArray(n.userData.originalMaterialArray)&&mats.length===1)n.material=n.material[0];
      const current=Array.isArray(n.material)?n.material:[n.material];
      for(const m of current)materials.push({m,node:n,original:{transparent:m.transparent,opacity:m.opacity,depthWrite:m.depthWrite,wireframe:m.wireframe||false,side:m.side,colorWrite:m.colorWrite,polygonOffset:m.polygonOffset,polygonOffsetFactor:m.polygonOffsetFactor,polygonOffsetUnits:m.polygonOffsetUnits}});
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
    $('#loaded-file').textContent=catalog[id].component?id+'/model.glb':id+'.glb';$('#clip-count').textContent=gltf.animations.length;
    $('#binding-status').textContent=driver.missing.length?driver.missing.length+' unresolved bindings':'All exported controls bound';
    if(driver.missing.length)throw new Error('Unresolved animation bindings: '+JSON.stringify(driver.missing));
    buildLoadoutControls();applyLoadout(loadouts.defaultValues);applyView(view);selectPresetButton('PARKED');cameraView('hero',false);
    $('#loading').classList.add('hidden');for(const b of $$('.transport button'))b.disabled=false;
    $('#asset').value=id;$('#coordinate-label').textContent='ONE SHARED AIRFRAME · TRUE METRES · Y UP';window.C130_REVIEW={model:id,revision:articulation.revision,inventoryMeshCount:meshCount,inventoryTriangles:triangles,clips:gltf.animations.length,bindings:driver.missing,controller,driver,scene:gltf.scene,loadouts,applyLoadout,selection:{...loadouts.selection},visibleMeshes:visibleMeshStats(gltf.scene).meshes,visibleTriangles:visibleMeshStats(gltf.scene).triangles};
    dispatchEvent(new CustomEvent('c130:model-loaded',{detail:{id,meshCount,triangles,clips:gltf.animations.length}}));
  }catch(e){if(token!==loadToken)return;console.error(e);showError(e.message);}
}
function buildLoadoutControls(){
  const presets=$('#loadout-preset');presets.replaceChildren();
  const custom=document.createElement('option');custom.value='';custom.textContent='Custom JCNC loadout';custom.disabled=true;presets.append(custom);
  for(const preset of loadouts.catalog.presets||[]){const option=document.createElement('option');option.value=preset.id;option.textContent=preset.label;presets.append(option);}
  const panel=$('#loadout-slots');panel.replaceChildren();
  for(const slot of loadouts.catalog.slots){
    const label=document.createElement('label');label.className='loadout-slot';
    const title=document.createElement('span');title.textContent=slot.label;label.append(title);
    const select=document.createElement('select');select.dataset.slot=slot.id;select.setAttribute('aria-label',slot.label);
    for(const item of slot.options){const option=document.createElement('option');option.value=item.id;option.textContent=item.label;select.append(option);}
    select.addEventListener('change',()=>{try{applyLoadout({...loadouts.selection,[slot.id]:select.value});}catch(e){select.value=loadouts.selection[slot.id];loadoutError(e.message);}});
    const note=document.createElement('small');note.dataset.slotNote=slot.id;label.append(select,note);panel.append(label);
  }
  const cameraSelect=$('#equipment-camera');cameraSelect.replaceChildren();
  const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='Inspect equipment…';cameraSelect.append(placeholder);
  const seen=new Set();
  for(const camera of [...(articulation.cameras||[]),...(loadouts.catalog.cameras||[])]){
    const id=camera.id||camera.name;if(!id||seen.has(id)||['hero','side','front','top','ramp','doors'].includes(id))continue;seen.add(id);
    const option=document.createElement('option');option.value=id;option.textContent=camera.label||id.replaceAll('_',' ');cameraSelect.append(option);
  }
}
function loadoutError(message){const el=$('#loadout-message');el.textContent=message;el.hidden=false;el.classList.add('error');}
function applyLoadout(values){
  const result=loadouts.apply(values,{beforeApply:()=>{controller?.reset();if(controller&&driver)driver.apply(controller.snapshot());}});
  activeArticulation=loadouts.activeArticulation();controller=new PresentationController(activeArticulation);
  driver.apply(controller.snapshot());
  $('#loadout-preset').value=result.preset&&!result.violations.length?result.preset.id:'';
  $('#loadout-badge').textContent=result.classification==='CUSTOM_JCNC'?'CUSTOM JCNC':result.classification==='HISTORICAL'?'HISTORICAL PRESET':'REFERENCE-GUIDED PRESET';
  $('#loadout-badge').classList.toggle('custom',result.classification==='CUSTOM_JCNC');
  $('#model-designation').textContent=result.label;
  $('#loadout-note').textContent=result.preset&&!result.violations.length?(result.preset.note||'Reference-guided visual configuration; acceptance remains in review.'):'This is a custom game configuration. It is not an accepted real-aircraft fit.';
  const message=$('#loadout-message');message.classList.remove('error');message.textContent=result.violations.map(v=>v.message).join(' ');message.hidden=!result.violations.length;
  for(const select of $$('[data-slot]'))select.value=result.selection[select.dataset.slot];
  for(const slot of loadouts.catalog.slots){const option=slot.options.find(o=>o.id===result.selection[slot.id]);const note=$$('[data-slot-note]').find(n=>n.dataset.slotNote===slot.id);note.textContent=option.note||'';note.hidden=!option.note;}
  const stats=visibleMeshStats(loaded.scene);
  $('#mesh-count').textContent=stats.meshes+' MESH PARTS / ARTICULATED';$('#triangle-count').textContent=Math.round(stats.triangles).toLocaleString()+' TRIANGLES';
  $('#control-count').textContent=activeArticulation.controls.length;
  $('#active-configuration').textContent=result.label;
  for(const button of $$('[data-module-slots]')){const fitted=button.dataset.moduleSlots.split(',').some(id=>result.selection[id]&&result.selection[id]!=='none');button.disabled=!fitted;button.title=fitted?'Inspect selected equipment':'Choose this equipment in Loadouts to inspect it';}
  rebuildControls();configureFireControls();selectPresetButton('PARKED');updateUI(controller.snapshot());
  if(window.C130_REVIEW)Object.assign(window.C130_REVIEW,{controller,selection:{...result.selection},visibleMeshes:stats.meshes,visibleTriangles:stats.triangles});
  dispatchEvent(new CustomEvent('c130:loadout-changed',{detail:{selection:{...result.selection},classification:result.classification,visibleMeshes:stats.meshes,visibleTriangles:stats.triangles,activeControls:activeArticulation.controls.length}}));
  return result;
}
function downloadLoadout(){const blob=new Blob([loadouts.serialize()],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='C130-loadout-r0004.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function rebuildControls(){
  const list=$('#mechanism-list');list.replaceChildren();const groups=new Map();
  for(const c of activeArticulation.controls){const key=c.group||'Mechanisms';if(!groups.has(key))groups.set(key,[]);groups.get(key).push(c);}
  for(const [name,items]of groups){
    const group=document.createElement('section');group.className='mechanism-group';
    const title=document.createElement('div');title.className='group-title';title.textContent=name.replaceAll('_',' ');const count=document.createElement('span');count.textContent=items.length;title.append(count);group.append(title);
    for(const c of items){
      const row=document.createElement('div');row.className='mechanism';row.dataset.control=c.id;row.dataset.search=(c.id+' '+c.label+' '+name).toLowerCase();
      const top=document.createElement('div');top.className='mechanism-top';const label=document.createElement('label');label.htmlFor='ctl-'+c.id;label.textContent=c.label||c.id;const out=document.createElement('output');out.id='out-'+c.id;out.textContent='0%';top.append(label,out);
      const input=document.createElement('input');input.type='range';input.id='ctl-'+c.id;input.min=0;input.max=1;input.step=.001;input.value=0;input.setAttribute('aria-label',c.label||c.id);input.addEventListener('input',()=>{controller.set(c.id,+input.value);selectPresetButton(null);});
      const endpoints=document.createElement('small');const lo=document.createElement('span'),hi=document.createElement('span');lo.textContent=c.states?.rest||'Rest';hi.textContent=c.kind==='cycle'?'Cycle complete':c.kind==='continuous'?'Running':c.states?.deployed||'Deployed';endpoints.append(lo,hi);
      const reason=document.createElement('div');reason.className='block-reason';row.append(top,input,endpoints,reason);group.append(row);
    }
    list.append(group);
  }
  filterControls();
}
function configureFireControls(){
  const a=controller.byId.has('gun30_fire_cycle'),b=controller.byId.has('gun105_fire_cycle');
  $('#firing-panel').hidden=!(a||b);
  $('#fire30').disabled=!a;$('#fire105').disabled=!b;
  for(const el of $$('[data-gun]'))el.disabled=!controller.byId.has(el.dataset.gun+'_fire_cycle');
  for(const el of $$('[data-aircraft-only]'))el.hidden=!!catalog[activeId].component;
  $('#fire-caption').textContent=a&&b?'30 mm cases enter the cabin collection bag. 105 mm cases move into the cabin handling area.':a?'Spent cases enter the internal collection bag.':'Spent cases leave the breech into the cabin handling area.';
}
function filterControls(){const term=$('#filter').value.toLowerCase();for(const row of $$('.mechanism'))row.hidden=!row.dataset.search.includes(term);for(const g of $$('.mechanism-group'))g.hidden=!Array.from(g.querySelectorAll('.mechanism')).some(r=>!r.hidden);}
function selectPresetButton(mode){for(const b of $$('[data-preset]'))b.classList.toggle('selected',b.dataset.preset===mode);}
function isSystemMesh(n){return catalog[activeId]?.component||/gun30|gun105|sensor|eoir|case_|casing|shell_case|collector|GAU23|M102|TANKER|DROGUE|HOSE|JATO|FULTON|SKYHOOK|REFUEL|RECEIVER/i.test(n.name);}
function applyView(mode){view=mode;for(const r of materials){const m=r.m,o=r.original;m.wireframe=false;m.transparent=o.transparent;m.opacity=o.opacity;m.depthWrite=o.depthWrite;m.side=o.side;m.colorWrite=o.colorWrite;m.polygonOffset=o.polygonOffset;m.polygonOffsetFactor=o.polygonOffsetFactor;m.polygonOffsetUnits=o.polygonOffsetUnits;if(mode==='wireframe'){m.transparent=false;m.opacity=1;m.colorWrite=false;m.depthWrite=true;m.polygonOffset=true;m.polygonOffsetFactor=1;m.polygonOffsetUnits=1;}if(mode==='xray'&&!isSystemMesh(r.node)){m.transparent=true;m.opacity=.12;m.depthWrite=false;m.side=THREE.DoubleSide;}m.needsUpdate=true;}loaded?.scene.traverse(n=>{if(n.userData.qaEdges?.isObject3D)n.userData.qaEdges.visible=mode==='xray';if(n.userData.qaTopology?.isObject3D)n.userData.qaTopology.visible=mode==='wireframe';});for(const b of $$('[data-view]'))b.classList.toggle('selected',b.dataset.view===mode);ground.visible=mode==='surface';}
function cameraView(name,animate=true){
  const center=modelBounds?modelBounds.getCenter(new THREE.Vector3()):new THREE.Vector3(0,5,0);
  const poses={hero:{p:[-47,26,-43],t:[0,5,0]},side:{p:[-66,8,0],t:[0,5,0]},front:{p:[0,9,-66],t:[0,5,-1]},top:{p:[0,77,.01],t:[0,0,0]},doors:{p:[-15,8,-15],t:[-1.2,3.5,-8]},ramp:{p:[-14,8,28],t:[0,3.2,10]}};
  if(catalog[activeId]?.component){
    const size=modelBounds.getSize(new THREE.Vector3()).length(),d=Math.max(size,1)*1.4;
    const t=center.toArray();
    Object.assign(poses,{hero:{p:[center.x-d,center.y+d*.55,center.z+d*.75],t},side:{p:[center.x,center.y+d*.1,center.z+d],t},front:{p:[center.x-d,center.y+d*.1,center.z],t},top:{p:[center.x,center.y+d,center.z+.001],t}});
  }
  for(const c of [...(articulation?.cameras||[]),...(loadouts?.catalog.cameras||[])]){
    const key=c.id||c.name;if(!key)continue;
    let target=c.target||c.look_at;
    if(c.target_node){const n=loaded.scene.getObjectByName(c.target_node);if(n)target=n.getWorldPosition(new THREE.Vector3()).toArray();}
    if(!target)continue;
    const position=c.position||c.offset?.map((v,i)=>v+target[i]);
    if(position)poses[key]={p:position,t:target};
  }
  for(const [cid,fallback] of [['gun30',[-2,2.55,-7.72]],['gun105',[-1.93,2.2,2.35]]]){
    const node=loaded?.scene.getObjectByName('PIVOT_'+cid+'_pitch')||loaded?.scene.getObjectByName(cid+'_MUZZLE_VISUAL_SOCKET');
    const target=node?node.getWorldPosition(new THREE.Vector3()).toArray():fallback;
    if(!poses[cid])poses[cid]={t:target,p:[target[0]-3.3,target[1]+.8,target[2]+1.8]};
    const ejected=loaded?.scene.getObjectByName(cid+'_CASE_EJECT_SOCKET');
    const inside=ejected?ejected.getWorldPosition(new THREE.Vector3()).toArray():[target[0]+1.1,target[1],target[2]];
    if(!poses[cid+'_inside'])poses[cid+'_inside']={t:inside,p:[inside[0]+1.6,inside[1]+.65,inside[2]+1.3]};
  }
  const pose=poses[name]||poses.hero;const p=new THREE.Vector3(...pose.p),t=new THREE.Vector3(...pose.t);
  if(name.endsWith('_inside')&&!catalog[activeId]?.component)applyView('xray');
  if(animate)cameraTween={from:camera.position.clone(),to:p,targetFrom:orbit.target.clone(),targetTo:t,start:performance.now(),duration:650};else{camera.position.copy(p);orbit.target.copy(t);orbit.update();}
  for(const b of $$('[data-camera]'))b.classList.toggle('selected',b.dataset.camera===name);
}
function updateUI(snapshot){
  $('#transport-status').textContent=snapshot.message;$('#pause').textContent=snapshot.paused?'Resume':'Pause';$('#direction-icon').textContent=snapshot.paused?'Ⅱ':snapshot.direction<0?'◀':snapshot.running?'▶':'●';
  $('#global-progress').style.width=(snapshot.globalTime*100)+'%';
  const playing=Object.entries(snapshot.firing||{}).filter(([,v])=>v.active).map(([id,v])=>(id.startsWith('gun30')?'30 mm':'105 mm')+' · '+Math.min(v.count,Math.floor(v.time)+1)+' / '+v.count);
  $('#firing-state').textContent=playing.length?playing.join(' / '):'Ready';
  for(const c of activeArticulation.controls){const row=$('[data-control="'+c.id+'"]'),input=$('#ctl-'+c.id),out=$('#out-'+c.id);if(!row)continue;const v=snapshot.values[c.id]||0;if(document.activeElement!==input)input.value=v;out.textContent=Math.round(v*100)+'%';const blocked=snapshot.blocked[c.id];row.classList.toggle('blocked',!!blocked);row.querySelector('.block-reason').textContent=blocked||'';}
}
$('#loadout-preset').addEventListener('change',e=>{const preset=loadouts?.presets.get(e.target.value);if(preset)applyLoadout(preset.values);});
$('#loadout-export').addEventListener('click',()=>{if(loadouts)downloadLoadout();});
$('#loadout-import').addEventListener('click',()=>$('#loadout-file').click());
$('#loadout-file').addEventListener('change',async e=>{const file=e.target.files[0];if(!file||!loadouts)return;try{if(file.size>100000)throw new Error('Choose a C-130 loadout JSON file smaller than 100 kB.');applyLoadout(loadouts.parse(await file.text()));}catch(error){loadoutError(error.message);}finally{e.target.value='';}});
$('#equipment-camera').addEventListener('change',e=>{if(e.target.value)cameraView(e.target.value);});
$('#fire30').addEventListener('click',()=>{controller?.fire('gun30_fire_cycle',3);selectPresetButton(null);});
$('#fire105').addEventListener('click',()=>{controller?.fire('gun105_fire_cycle',1);selectPresetButton(null);});
$('#asset').addEventListener('change',e=>loadAsset(e.target.value));$('#filter').addEventListener('input',filterControls);
for(const b of $$('[data-camera]'))b.addEventListener('click',()=>cameraView(b.dataset.camera));
for(const b of $$('[data-view]'))b.addEventListener('click',()=>applyView(b.dataset.view));
for(const b of $$('[data-preset]'))b.addEventListener('click',()=>{controller?.preset(b.dataset.preset);selectPresetButton(b.dataset.preset);});
$('#actuate').addEventListener('click',()=>{controller?.actuateEverything();selectPresetButton(null);});$('#pause').addEventListener('click',()=>controller?.togglePause());$('#reverse').addEventListener('click',()=>controller?.reverse());$('#reset').addEventListener('click',()=>{controller?.reset();selectPresetButton('PARKED');});
$('#default').addEventListener('click',()=>{if(loadouts)applyLoadout(loadouts.defaultValues);else controller?.reset();selectPresetButton('PARKED');applyView('surface');cameraView('hero');});
orbit.addEventListener('start',()=>{cameraTween=null;for(const b of $$('[data-camera]'))b.classList.remove('selected');});
function frame(now){
  const dt=Math.min((now-lastTime)/1000,.1);lastTime=now;
  if(controller&&driver){const state=controller.tick(dt);driver.apply(state);if(frameId%3===0)updateUI(state);}
  if(cameraTween){const raw=Math.min((now-cameraTween.start)/cameraTween.duration,1),t=raw*raw*(3-2*raw);camera.position.lerpVectors(cameraTween.from,cameraTween.to,t);orbit.target.lerpVectors(cameraTween.targetFrom,cameraTween.targetTo,t);if(raw===1)cameraTween=null;}
  orbit.update();renderer.render(scene,camera);frameId++;requestAnimationFrame(frame);
}
const requestedAsset=new URLSearchParams(location.search).get('asset');
const initialAsset=requestedAsset in catalog&&(!bundle||requestedAsset in bundle.models)?requestedAsset:bundle?.default_asset||'c130-family';
requestAnimationFrame(frame);loadAsset(initialAsset);
