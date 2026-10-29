/** claude-design | Behavioral tests of scheduling, state recovery and arbitration. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import { PresentationController } from './controller.mjs';

const controls=[
 {id:'gear_nose',kind:'rotation',duration:2},
 {id:'gear_left',kind:'rotation',duration:2},
 {id:'gear_right',kind:'rotation',duration:2},
 {id:'nose_gear_door',kind:'rotation',duration:1,role:'gear_door',enabled_if:{control:'gear_nose',equals:0}},
 {id:'cargo_ramp',kind:'rotation',duration:2,role:'access'},
 {id:'cargo_upper_door',kind:'rotation',duration:2,role:'access',owned_by:'cargo_ramp',enabled_if:{control:'cargo_ramp',equals:0}},
 {id:'crew_door',kind:'rotation',duration:2,role:'access'},
 {id:'flaps',kind:'rotation',duration:2},
 {id:'rudder',kind:'rotation',duration:2},
 {id:'prop_1',kind:'continuous',duration:1},
 {id:'sensor_yaw',kind:'rotation',duration:2}
];
const c=new PresentationController({controls});
function run(seconds,fn=()=>{}){for(let i=0;i<Math.ceil(seconds*60);i++){c.tick(1/60);fn(c.snapshot());}}
c.actuateEverything();
let accessMaximum=0,gearMaximum=0,simultaneous=false;
run(25,s=>{
 accessMaximum=Math.max(accessMaximum,s.values.cargo_ramp);gearMaximum=Math.max(gearMaximum,s.values.gear_nose);
 if(s.values.flaps>.1&&s.values.sensor_yaw>.1)simultaneous=true;
 if(s.values.gear_nose>.002)assert(s.values.cargo_ramp<=.002,'Access must close before gear retracts');
 if(s.values.nose_gear_door>.002)assert(s.values.gear_nose<=.002,'Standalone gear door owns channel only while gear at rest');
 if(s.values.cargo_upper_door>.002)assert(s.values.cargo_ramp<=.002,'Standalone cargo door owns its channel only while cargo master at rest');
});
assert(accessMaximum>.98,'Global demonstration must reach access full opening');
assert(gearMaximum>.98,'Global demonstration must fully retract gear');assert(simultaneous);
assert.equal(c.covered.size,controls.length,'Every declared control must be exercised');
c.togglePause();const paused=JSON.stringify(c.snapshot());run(2);assert.equal(JSON.stringify(c.snapshot()),paused,'Pause freezes phases and transforms');
c.reverse();run(25);assert(Object.values(c.values).every(v=>v===0),'Reverse returns through canonical state');
c.preset('SERVICE');run(4);assert(c.values.cargo_ramp===1);
c.preset('FLYING');let sawBlocked=false;
run(5,s=>{if(s.blocked.gear_nose)sawBlocked=true;if(s.values.gear_nose>.002)assert(s.values.cargo_ramp<=.002);});
assert(sawBlocked,'Flying transition should visibly wait for access');assert(c.values.gear_nose>.99);
c.reset();assert(Object.values(c.values).every(v=>v===0));assert(Object.values(c.phases).every(v=>v===0));assert.equal(c.running,false);
c.set('cargo_ramp',1);run(3);c.actuateEverything();assert(c.preparing,'Global mode must recover current pose before demonstration');run(29);assert(c.values.gear_nose>.99);
const report={author:'claude-design',status:'PASS',controller_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL('./controller.mjs',import.meta.url))).digest('hex'),checks:['coverage','concurrent channels','gear/access sequencing','standalone door arbitration','pause freezes continuous phase','reverse recovery','preset transition','canonical reset','start from nonrest pose'],scope:'controller behavior only; no GPU or geometric clearance claim'};
fs.writeFileSync(new URL('./controller-qa.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
