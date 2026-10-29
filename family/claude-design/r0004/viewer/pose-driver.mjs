/** claude-design | Apply current GLB animation tracks, preserving its canonical rest. */
import * as THREE from 'three';

export class PoseDriver {
  constructor(scene,clips,articulation) {
    this.scene=scene; this.controls=articulation.controls||[];
    this.rest=new Map(); this.clips=new Map(); this.missing=[];
    scene.traverse(n=>this.rest.set(n.uuid,{node:n,position:n.position.clone(),quaternion:n.quaternion.clone(),scale:n.scale.clone(),morphTargetInfluences:n.morphTargetInfluences?Array.from(n.morphTargetInfluences):null}));
    for(const clip of clips) {
      const tracks=[];
      for(const track of clip.tracks) {
        const parsed=THREE.PropertyBinding.parseTrackName(track.name);
        const node=THREE.PropertyBinding.findNode(scene,parsed.nodeName);
        if(!node){this.missing.push({clip:clip.name,track:track.name});continue;}
        tracks.push({node,property:parsed.propertyName,interpolant:track.createInterpolant(),size:track.getValueSize()});
      }
      this.clips.set(clip.name,{duration:clip.duration,tracks});
    }
    for(const c of this.controls) {
      if(!this.clips.has(c.clip||c.id))this.missing.push({control:c.id,clip:c.clip||c.id});
      if(c.node&&!scene.getObjectByName(c.node))this.missing.push({control:c.id,node:c.node});
    }
  }
  apply(snapshot) {
    for(const r of this.rest.values()){
      r.node.position.copy(r.position); r.node.quaternion.copy(r.quaternion); r.node.scale.copy(r.scale);
      if(r.morphTargetInfluences){for(let i=0;i<r.morphTargetInfluences.length;i++)r.node.morphTargetInfluences[i]=r.morphTargetInfluences[i];}
    }
    for(const c of this.controls) {
      const v=c.kind==='continuous'?(snapshot.phases[c.id]||0):(snapshot.values[c.id]||0);
      if(v<=1e-8) continue;
      const clip=this.clips.get(c.clip||c.id); if(!clip)continue;
      const time=Math.max(0,Math.min(clip.duration,v*clip.duration));
      for(const t of clip.tracks){
        const sample=t.interpolant.evaluate(time);
        if(t.property==='quaternion')t.node.quaternion.fromArray(sample).normalize();
        else if(t.property==='position')t.node.position.fromArray(sample);
        else if(t.property==='scale')t.node.scale.fromArray(sample);
        else if(t.property==='morphTargetInfluences')t.node.morphTargetInfluences=Array.from(sample);
      }
    }
    this.scene.updateMatrixWorld(true);
  }
}
