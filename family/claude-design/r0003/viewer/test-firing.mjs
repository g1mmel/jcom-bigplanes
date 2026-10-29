/** claude-design | Deterministic visual firing presentation, not weapon simulation. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {PresentationController} from './controller.mjs';
const fixture={controls:[
  {id:'gun30_recoil',kind:'translation',duration:1,owned_by:'gun30_fire_cycle'},
  {id:'gun105_recoil',kind:'translation',duration:1,owned_by:'gun105_fire_cycle'},
  {id:'gun30_fire_cycle',kind:'cycle',duration:.9,preview_cycles:6},
  {id:'gun105_fire_cycle',kind:'cycle',duration:3.4,preview_cycles:2},
  {id:'sensor_yaw',kind:'rotation',duration:1.5}
]};
const c=new PresentationController(fixture);
const advance=(seconds,fn=()=>{})=>{for(let i=0;i<Math.round(seconds*120);i++){const s=c.tick(1/120);fn(s);}};
c.set('gun30_recoil',1);advance(1.2);assert.equal(c.values.gun30_recoil,1);
c.fire('gun30_fire_cycle',3);advance(.3);
assert.equal(c.firing.gun30_fire_cycle.time,0,'Fire must wait for manual recoil to return');
advance(.8);assert(c.firing.gun30_fire_cycle.time>0,'Fire should begin once inspection is at rest');
const playState=JSON.stringify(c.snapshot());c.togglePause();const paused=JSON.stringify(c.snapshot());advance(2);assert.equal(JSON.stringify(c.snapshot()),paused,'Pause freezes current shot, case and flash phase');
c.togglePause();const phase=c.values.gun30_fire_cycle;advance(.1);assert.notEqual(c.values.gun30_fire_cycle,phase);
c.reverse();assert.equal(c.direction,-1);advance(.1);assert(Math.abs(c.values.gun30_fire_cycle-phase)<1e-9,'Interrupted reverse returns same presentation phase');
advance(4);assert.equal(c.values.gun30_fire_cycle,0);assert.equal(c.firing.gun30_fire_cycle.time,0);assert(!c.firing.gun30_fire_cycle.active);
c.reset();c.fire('gun30_fire_cycle',3);let wraps=0,last=0;
advance(3,s=>{const v=s.values.gun30_fire_cycle;assert(v>=0&&v<=1);if(v<last-.5)wraps++;last=v;assert.equal(s.values.gun30_recoil,0);});
assert.equal(wraps,3,'Burst must complete exactly its authored three visual cycles');
assert.equal(c.firing.gun30_fire_cycle.time,3);assert.equal(c.values.gun30_fire_cycle,0);
c.reverse();advance(3);assert.equal(c.firing.gun30_fire_cycle.time,0,'Reverse replay completes at zero');
c.reset();c.fire('gun105_fire_cycle',1);advance(4);assert.equal(c.firing.gun105_fire_cycle.time,1);assert.equal(c.values.gun105_fire_cycle,0,'Single 105 cycle must return to canonical rest');
c.reset();c.fire('gun30_fire_cycle',3);c.fire('gun105_fire_cycle',1);advance(.4);
assert(c.values.gun30_fire_cycle>0&&c.values.gun105_fire_cycle>0,'Compatible gun presentations can run concurrently');
const prior105=c.firing.gun105_fire_cycle.time;c.set('sensor_yaw',.4);advance(.1);assert(c.firing.gun105_fire_cycle.time>prior105,'Unrelated sensor control must not freeze active cases');
c.set('gun30_recoil',.4);assert(!c.firing.gun30_fire_cycle);assert.equal(c.values.gun30_fire_cycle,0);assert(c.firing.gun105_fire_cycle.active,'Inspection cancels only its owning firing cycle');
c.reset();assert.deepEqual(c.firing,{});assert(Object.values(c.values).every(v=>v===0));
c.actuateEverything();advance(11.8);assert(c.values.gun105_fire_cycle>.01);c.fire('gun30_fire_cycle',3);assert.equal(c.values.gun105_fire_cycle,0,'Manual fire must clear transient cases left by ALL');assert.equal(c.targets.gun105_fire_cycle,0);
c.reset();c.actuateEverything();advance(11.8);c.set('sensor_yaw',.4);assert.equal(c.values.gun30_fire_cycle,0);assert.equal(c.values.gun105_fire_cycle,0,'Leaving ALL for manual controls must not suspend cases');
c.set('gun105_fire_cycle',.6);c.fire('gun30_fire_cycle',3);assert.equal(c.values.gun105_fire_cycle,0,'Live fire clears inactive frame-inspection case poses');
advance(.2);c.fire('gun30_fire_cycle',3);assert.equal(Object.keys(c.firing).length,1,'Repeated activation reuses one instance');assert.equal(c.values.gun30_fire_cycle,0);advance(.1);c.preset('PARKED');assert.equal(c.values.gun30_fire_cycle,0);assert.deepEqual(c.firing,{});
c.fire('gun105_fire_cycle',1);advance(.3);c.actuateEverything();assert.equal(c.values.gun105_fire_cycle,0);assert.deepEqual(c.firing,{});
c.reset();
c.actuateEverything();advance(25,s=>{for(const control of fixture.controls){if(control.owned_by&&s.values[control.id]>.002)assert(s.values[control.owned_by]<=.002,'Cycle/inspection ownership conflict');}});
assert.equal(c.covered.size,fixture.controls.length,'All-actuation must include cycles and inspection controls');
c.reverse();advance(25);assert(Object.values(c.values).every(v=>v===0));
const report={author:'claude-design',status:'PASS',controller_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL('./controller.mjs',import.meta.url))).digest('hex'),checks:['manual recoil recovery before firing','pause freezes firing timeline','interrupted reverse returns identical phase','three visual cycles exactly','single shot and burst can run concurrently','full reverse playback','cycle and manual ownership arbitration','Actuate everything coverage','reset clears all firing instances','ALL-to-manual clears transient cases','repeated fire reuses one cycle instance','preset and restart clear firing poses'],scope:'Scheduling only. Actual model bindings and geometry are tested separately; no browser rendering, ballistic or native-engine claim.'};
fs.writeFileSync(new URL('./firing-controller-qa.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
