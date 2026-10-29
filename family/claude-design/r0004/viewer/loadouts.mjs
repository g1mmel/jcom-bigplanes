/** claude-design | One shared aircraft, atomic module choices and explicit provenance. */
const same = (a,b) => Object.keys(a).length===Object.keys(b).length && Object.entries(a).every(([key,value])=>b[key]===value);
const list = value => Array.isArray(value)?value:[value];

export function normalizeModuleScales(scene,catalog){
  // glTF has no standard visibility track. The exported default fit encodes unused
  // modules with a zero scale for generic importers. Restore authored module scale
  // BEFORE the pose driver captures rest; live selections use visibility instead.
  const names=new Set(catalog.slots.flatMap(s=>s.options.flatMap(o=>o.module_roots||[])));
  const nodes=[...names].map(name=>{const node=scene.getObjectByName(name);if(!node)throw new Error('Loadout module is absent from the model: '+name);return node;});
  for(const node of nodes){const scale=node.userData?.canonical_scale||[1,1,1];if(!Array.isArray(scale)||scale.length!==3||!scale.every(Number.isFinite))throw new Error('Invalid canonical module scale: '+node.name);node.scale?.fromArray(scale);}
  scene.updateMatrixWorld?.(true);
}

export class LoadoutManager {
  constructor(catalog,scene,articulation) {
    this.catalog=catalog;this.scene=scene;this.articulation=articulation;
    this.slots=new Map();this.roots=new Map();this.optionalControls=new Set();
    this.byControl=new Map((articulation.controls||[]).map(c=>[c.id,c]));
    if(!Array.isArray(catalog.slots)||!catalog.slots.length)throw new Error('The family has no loadout slots.');
    for(const slot of catalog.slots){
      if(this.slots.has(slot.id)||!slot.id)throw new Error('Duplicate or empty loadout slot: '+slot.id);
      if(!Array.isArray(slot.options)||!slot.options.length)throw new Error('No choices for loadout slot '+slot.id);
      const options=new Map();
      for(const option of slot.options){
        if(options.has(option.id)||!option.id)throw new Error('Duplicate or empty option in '+slot.id);
        options.set(option.id,option);
        for(const name of option.module_roots||[]){
          const node=scene.getObjectByName(name);
          if(!node)throw new Error('Loadout module is absent from the model: '+name);
          this.roots.set(name,node);
        }
        for(const id of option.control_ids||[]){
          if(!this.byControl.has(id))throw new Error('Loadout control is absent: '+id);
          this.optionalControls.add(id);
        }
      }
      this.slots.set(slot.id,{...slot,options});
    }
    this.presets=new Map();
    for(const preset of catalog.presets||[]){
      if(this.presets.has(preset.id))throw new Error('Duplicate loadout preset: '+preset.id);
      this.validate(preset.values);this.presets.set(preset.id,preset);
    }
    const first=this.presets.get(catalog.default_preset)||this.presets.values().next().value;
    this.defaultValues=first?{...first.values}:Object.fromEntries([...this.slots].map(([id,s])=>[id,s.options.keys().next().value]));
    this.selection=null;
  }
  validate(values){
    if(!values||typeof values!=='object'||Array.isArray(values))throw new Error('Loadout values must be an object.');
    for(const key of Object.keys(values))if(!this.slots.has(key))throw new Error('Unknown loadout slot: '+key);
    for(const [id,slot] of this.slots)if(!slot.options.has(values[id]))throw new Error('Choose a valid option for '+slot.label+': '+String(values[id]));
    return {...values};
  }
  options(values=this.selection||this.defaultValues){
    return [...this.slots].map(([id,slot])=>slot.options.get(values[id]));
  }
  activeControls(values=this.selection||this.defaultValues){
    const included=new Set(this.options(values).flatMap(o=>o.control_ids||[]));
    return (this.articulation.controls||[]).filter(c=>!this.optionalControls.has(c.id)||included.has(c.id));
  }
  activeArticulation(values=this.selection||this.defaultValues){
    return {...this.articulation,controls:this.activeControls(values)};
  }
  assess(values=this.selection||this.defaultValues){
    this.validate(values);
    const violations=[];
    for(const rule of this.catalog.constraints||[]){
      if(!Object.entries(rule.when||{}).every(([key,allowed])=>list(allowed).includes(values[key])))continue;
      const failed=Object.entries(rule.requires||{}).filter(([key,allowed])=>!list(allowed).includes(values[key]));
      if(failed.length)violations.push({id:rule.id,message:rule.message||'This combination is not a documented preset.',failed_slots:failed.map(([key])=>key)});
    }
    const preset=[...this.presets.values()].find(p=>same(p.values,values))||null;
    return {preset,violations,classification:preset&&!violations.length?(preset.status||'REFERENCE_GUIDED'):'CUSTOM_JCNC',label:preset&&!violations.length?preset.label:'Custom JCNC loadout'};
  }
  apply(values,{beforeApply}={}){
    const validated=this.validate(values);
    const selected=new Set(this.options(validated).flatMap(o=>o.module_roots||[]));
    // Resolve and validate everything before touching a live pose or visible module.
    const changes=[...this.roots].map(([name,node])=>({node,visible:selected.has(name)}));
    beforeApply?.();
    for(const {node,visible} of changes)node.visible=visible;
    this.selection=validated;
    this.scene.updateMatrixWorld?.(true);
    return {selection:{...validated},...this.assess(validated),controls:this.activeControls(validated)};
  }
  applyPreset(id,options){const preset=this.presets.get(id);if(!preset)throw new Error('Unknown loadout preset: '+id);return this.apply(preset.values,options);}
  reset(options){return this.apply(this.defaultValues,options);}
  serialize(){return JSON.stringify({format:'jcnc-c130-loadout',version:1,family_id:this.catalog.family_id,revision:this.catalog.revision,values:{...(this.selection||this.defaultValues)}},null,2)+'\n';}
  parse(input){
    const item=typeof input==='string'?JSON.parse(input):input;
    if(item?.format!=='jcnc-c130-loadout'||item.version!==1)throw new Error('This file is not a supported C-130 loadout.');
    if(item.family_id!==this.catalog.family_id)throw new Error('This loadout belongs to a different family.');
    if(item.revision!==this.catalog.revision)throw new Error('This loadout belongs to revision '+item.revision+'. Open it with the matching family revision.');
    return this.validate(item.values);
  }
}

export function visibleMeshStats(scene){
  let meshes=0,triangles=0;
  function visit(node,visible){
    visible=visible&&node.visible!==false;
    if(!visible)return;
    if(node.isMesh){meshes++;triangles+=(node.geometry.index?.count||node.geometry.attributes.position.count)/3;}
    for(const child of node.children||[])visit(child,visible);
  }
  visit(scene,true);
  return {meshes,triangles};
}
