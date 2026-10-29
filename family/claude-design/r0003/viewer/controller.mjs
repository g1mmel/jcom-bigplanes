/** claude-design | Deterministic normalized presentation state; no DOM dependency. */
export const clamp = (x, a=0, b=1) => Math.min(b, Math.max(a, Number.isFinite(+x) ? +x : a));
export const smooth = x => { x=clamp(x); return x*x*(3-2*x); };
const range = (x,a,b) => clamp((x-a)/(b-a));

export function isGear(c) { return /^gear_(nose|left|right)$/.test(c.id) || c.role==='gear_sequence'; }
export function isGearDoor(c) { return c.role==='gear_door' || /gear.*door|door.*gear/.test(c.id) || c.group==='gear_doors'; }
export function isAccess(c) { return c.role==='access' || /ramp|cargo|crew_door|paratroop|exit_door|rear_cover/.test(c.id) || /access|cargo/.test(c.group||''); }
export function isInspection(c) { return isGearDoor(c) || Boolean(c.owned_by); }
export function conditions(c) {
  if (!c.enabled_if) return [];
  return Array.isArray(c.enabled_if) ? c.enabled_if : [c.enabled_if];
}

export class PresentationController {
  constructor(articulation) {
    this.articulation=articulation;
    this.controls=(articulation.controls||[]).map(c=>({...c}));
    this.byId=new Map(this.controls.map(c=>[c.id,c]));
    if (this.byId.size!==this.controls.length) throw new Error('Duplicate control ID');
    this.reset();
  }
  reset() {
    this.values=Object.fromEntries(this.controls.map(c=>[c.id,0]));
    this.targets={...this.values};
    this.phases=Object.fromEntries(this.controls.filter(c=>c.kind==='continuous').map(c=>[c.id,0]));
    this.blocked={}; this.mode='PARKED'; this.running=false; this.paused=false;
    this.direction=1; this.globalTime=0; this.elapsed=0; this.globalDuration=24; this.preparing=false;
    this.message='Canonical parked state'; this.covered=new Set(); this.firing={};
  }
  clearTransientCycles(keepActive=false) {
    for(const c of this.controls)if(c.kind==='cycle'&&(!keepActive||!this.firing[c.id]?.active)){this.values[c.id]=0;this.targets[c.id]=0;}
  }
  set(id,value) {
    const c=this.byId.get(id); if (!c) throw new Error('Unknown control '+id);
    if(this.mode==='ALL')this.clearTransientCycles();
    const ownedCycle=c.kind==='cycle'?id:(this.byId.get(c.owned_by)?.kind==='cycle'?c.owned_by:null);
    if(ownedCycle){delete this.firing[ownedCycle];this.values[ownedCycle]=0;this.targets[ownedCycle]=0;}
    this.running=Object.values(this.firing).some(f=>f.active);this.mode=this.running?'FIRE':'CUSTOM';this.paused=false;
    this.targets[id]=clamp(value); this.message=c.kind==='cycle'?'Firing cycle inspection':'Manual controls';
    if(c.kind==='cycle') this.values[id]=this.targets[id];
    if(value>0){for(const other of this.controls)if(other.owned_by===id)this.targets[other.id]=0;if(c.owned_by)this.targets[c.owned_by]=0;}
    if (isGear(c) && value>0) {
      for (const other of this.controls) if (isAccess(other) || isGearDoor(other)) this.targets[other.id]=0;
    }
    if (isAccess(c) && value>0) for (const other of this.controls) {
      if (isGear(other)||other.kind==='continuous') this.targets[other.id]=0;
    }
    this.arbitrateTargets();
  }
  preset(name) {
    const upper=String(name).toUpperCase(); this.mode=upper; this.running=false; this.paused=false;
    this.targets=Object.fromEntries(this.controls.map(c=>[c.id,0])); this.firing={};this.clearTransientCycles();
    const presets=this.articulation.presets||{};
    let p=Array.isArray(presets)?presets.find(x=>String(x.id||x.name).toUpperCase()===upper):presets[upper]||presets[upper.toLowerCase()];
    p=p?.values||p?.controls||p;
    if (p && !Array.isArray(p)) {
      for (const [k,v] of Object.entries(p)) if(this.byId.has(k)) this.targets[k]=clamp(v);
    } else {
      for (const c of this.controls) {
        if (upper==='SERVICE'&&isAccess(c)) this.targets[c.id]=1;
        if (upper==='FLYING'&&(isGear(c)||c.kind==='continuous')) this.targets[c.id]=1;
      }
    }
    this.message=upper==='FLYING'?'Closing access before gear retraction':upper==='SERVICE'?'Stopping propellers; lowering gear before access':upper+' transition';
    this.arbitrateTargets();
  }
  actuateEverything() {
    this.clearTransientCycles();
    this.mode='ALL'; this.running=true; this.paused=false; this.direction=1;
    this.globalTime=0; this.firing={}; this.covered.clear(); this.preparing=Object.values(this.values).some(v=>v>.002);
    this.targets=Object.fromEntries(this.controls.map(c=>[c.id,0]));
    this.message=this.preparing?'Returning to rest before complete demonstration':'Concurrent mechanism demonstration';
  }
  fire(id,count=1) {
    const c=this.byId.get(id); if(!c||c.kind!=='cycle') throw new Error('Unknown visual firing cycle '+id);
    this.clearTransientCycles(true);
    this.mode='FIRE';this.running=true;this.paused=false;this.direction=1;this.preparing=false;this.globalTime=0;
    this.firing[id]={time:0,count:Math.max(1,Math.min(12,Math.round(count))),active:true};
    this.values[id]=0;this.targets[id]=0;
    for(const other of this.controls) if(other.owned_by===id)this.targets[other.id]=0;
    this.message=count>1?'Visual short burst · internal case collection':'Visual single shot · internal case handling';
  }
  togglePause() { this.paused=!this.paused; this.message=this.paused?'Paused — all motion frozen':'Presentation resumed'; }
  reverse() {
    if(this.mode==='FIRE'&&Object.keys(this.firing).length) {
      this.direction*=-1;this.running=true;this.paused=false;
      for(const f of Object.values(this.firing))f.active=true;
      this.message=this.direction<0?'Reverse firing presentation':'Forward firing presentation';return;
    }
    if (this.mode!=='ALL') {
      for (const c of this.controls) this.targets[c.id]=0;
      this.mode='CUSTOM'; this.paused=false; this.direction=-1; this.message='Returning through valid mechanism paths';
    } else {
      this.direction*=-1; this.running=true; this.paused=false;
      this.message=this.direction<0?'Reverse — staged recovery':'Forward — concurrent demonstration';
    }
  }
  enabled(c) {
    for (const rule of conditions(c)) {
      const v=this.values[rule.control]||0;
      if ('equals' in rule && Math.abs(v-rule.equals)>.002) return false;
      if ('max' in rule && v>rule.max+.002) return false;
      if ('min' in rule && v<rule.min-.002) return false;
    }
    if (isGearDoor(c) && this.controls.some(g=>isGear(g)&&this.values[g.id]>.002)) return false;
    if (isAccess(c) && this.controls.some(g=>(isGear(g)||g.kind==='continuous')&&this.values[g.id]>.002)) return false;
    return true;
  }
  arbitrateTargets() {
    this.blocked={};
    for(const c of this.controls)if(c.owned_by&&this.targets[c.owned_by]>.002&&this.targets[c.id]>.002)this.targets[c.id]=0;
    const accessActive=this.controls.some(c=>isAccess(c)&&this.values[c.id]>.002);
    const doorActive=this.controls.some(c=>isGearDoor(c)&&this.values[c.id]>.002);
    for (const c of this.controls) {
      if(this.targets[c.id]>.002 && this.controls.some(other=>other.owned_by===c.id&&this.values[other.id]>.002))this.blocked[c.id]='Waiting for standalone inspection control to return to rest';
      if (isGear(c)&&this.targets[c.id]>.002&&(accessActive||doorActive)) this.blocked[c.id]='Waiting for access and standalone gear doors to close';
      if (c.kind==='continuous'&&this.targets[c.id]>.002&&accessActive) this.blocked[c.id]='Waiting for personnel / cargo access to close';
      if ((isAccess(c)||isGearDoor(c))&&this.targets[c.id]>.002&&!this.enabled(c)) this.blocked[c.id]='Waiting for gear down and propellers stopped';
      if (conditions(c).length&&!this.enabled(c)) this.blocked[c.id]='Dependency not yet in its required state';
    }
  }
  globalTargets() {
    const t=this.globalTime;
    for (const c of this.controls) {
      let v;
      if(c.kind==='cycle') {
        const progress=range(t,.25,1)*(c.preview_cycles||(/30/.test(c.id)?6:2));
        v=t<=.25||t>=1?0:progress-Math.floor(progress);
      }
      else if (c.kind==='continuous') v=smooth(range(t,.61,.69));
      else if (isGear(c)) v=smooth(range(t,.65,1));
      else if (isInspection(c)) v=t<.12?smooth(range(t,0,.12)):1-smooth(range(t,.12,.24));
      else if (isAccess(c)) v=t<.42?smooth(range(t,.25,.42)):1-smooth(range(t,.42,.60));
      else v=smooth(t);
      this.targets[c.id]=v;
    }
    if (t<.24) this.message='Standalone closure inspection · compatible mechanisms move together';
    else if (t<.42) this.message='Opening staged cargo and personnel access';
    else if (t<.61) this.message='Closing access before propulsion and gear';
    else if (t<1) this.message='Propellers, flight controls and staged gear sequence';
  }
  tick(dt) {
    dt=clamp(dt,0,.1); if (this.paused||dt===0) return this.snapshot();
    this.elapsed+=dt;
    if(this.preparing && Object.values(this.values).every(v=>v<=.002))this.preparing=false;
    if(this.mode==='ALL'&&this.running&&!this.preparing) {
      this.globalTime=clamp(this.globalTime+dt*this.direction/this.globalDuration);
      this.globalTargets();
      if((this.direction>0&&this.globalTime>=1)||(this.direction<0&&this.globalTime<=0)) {
        this.running=false;
        if(this.globalTime<=0) { for(const c of this.controls) this.targets[c.id]=0; }
        this.message=this.direction>0?'Demonstration complete · propellers continue until Pause or Reset':'Recovered to canonical state';
      }
    }
    this.arbitrateTargets();
    for(const [id,f] of Object.entries(this.firing)) {
      if(!f.active)continue;
      const c=this.byId.get(id);
      if(this.controls.some(other=>other.owned_by===id&&this.values[other.id]>.002)){this.blocked[id]='Returning recoil inspection to its rest position';continue;}
      f.time=Math.max(0,Math.min(f.count,f.time+dt*this.direction/Math.max(.15,c.duration||1)));
      const terminal=this.direction>0?f.time>=f.count:f.time<=0;
      this.values[id]=this.targets[id]=terminal?0:f.time-Math.floor(f.time);
      if(terminal)f.active=false;
      if(this.values[id]>.9)this.covered.add(id);
    }
    if(this.mode==='FIRE'){this.running=Object.values(this.firing).some(f=>f.active);if(!this.running)this.message=this.direction>0?'Firing presentation complete · ready':'Firing presentation recovered to rest';}
    for (const c of this.controls) {
      const current=this.values[c.id], wanted=this.blocked[c.id]&&this.targets[c.id]>current?current:this.targets[c.id];
      const step=dt/Math.max(.15,c.duration||2.4);
      this.values[c.id]=this.mode==='ALL'&&!this.preparing?wanted:current+Math.sign(wanted-current)*Math.min(Math.abs(wanted-current),step);
      if(this.values[c.id]>(c.kind==='cycle'?.90:.98)) this.covered.add(c.id);
      if(c.kind==='continuous') {
        this.phases[c.id]=(this.phases[c.id]+dt*this.values[c.id]*(c.preview_rps||1.25)*this.direction)%1;
        if(this.phases[c.id]<0)this.phases[c.id]+=1;
      }
    }
    return this.snapshot();
  }
  snapshot() { return {values:{...this.values},phases:{...this.phases},blocked:{...this.blocked},mode:this.mode,running:this.running,paused:this.paused,direction:this.direction,globalTime:this.globalTime,message:this.message,covered:[...this.covered],firing:Object.fromEntries(Object.entries(this.firing).map(([id,f])=>[id,{...f}]))}; }
}
