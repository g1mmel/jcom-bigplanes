"""claude-design: aircraft-independent editable source and rebuild entrypoint."""
from pathlib import Path
import json, numpy as np
from gltf_core import GLB, quat
from gun_components import add_gun
from eoir_component import add_sensor

class Component:
    def __init__(self,cfg):
        self.id=cfg['id'];self.label=cfg['label'];self.glb=GLB(self.label);self.controls=[];self.mat={};self.log=[];self.known_pivots={0:np.zeros(3)};self.kit=0
        self.glb.doc['nodes'][0]['name']='INDEPENDENT_SYSTEM_ROOT'
        self.glb.doc['nodes'][0]['extras'].update(component=True,aircraft_dependency=False)
    def pivot(self,cid,pos,parent=0,extras=None):
        p=np.asarray(pos,float);i=self.glb.node('PIVOT_'+cid,parent=parent,translation=p-self.known_pivots.get(parent,np.zeros(3)),extras=extras);self.known_pivots[i]=p;return i
    def attach(self,mesh,pivot):return self.glb.mesh(mesh,parent=pivot,origin=self.known_pivots[pivot])
    def control(self,cid,label,pivot,axis,maximum,kind='rotation',duration=3,group='Mechanisms',ev=None,**kwargs):
        axis=np.asarray(axis,float);t=np.linspace(0,1,33);q=t*t*(3-2*t)
        rest=np.array(self.glb.doc['nodes'][pivot].get('translation',[0,0,0]))
        tracks=[(pivot,'translation',t,[rest+axis*maximum*u for u in q])] if kind=='translation' else [(pivot,'rotation',t,[quat(axis,maximum*u) for u in q])]
        self.glb.animation(cid,tracks);self.controls.append({'id':cid,'label':label,'node':self.glb.doc['nodes'][pivot]['name'],'clip':cid,'kind':kind,'duration':duration,'group':group,'min':0,'max':maximum,'rest':0,'axis':axis.tolist(),'evidence':ev,**kwargs})

def main():
    here=Path(__file__).resolve().parent;cfg=json.loads((here/'component.json').read_text());m=Component(cfg)
    if cfg['kind']=='sensor':add_sensor(m,'eoir',[0,0,0])
    else:add_gun(m,'gun105' if cfg['kind']=='105' else 'gun30',[0,0,0],cfg['kind']=='105')
    result=m.glb.write(here.parent/'model-rebuilt.glb')
    (here.parent/'rebuild-receipt.json').write_text(json.dumps({'author':'claude-design','output':result,'controls':m.controls,'firing_profiles':getattr(m,'firing_profiles',[]),'scope':'standalone source rebuilt without aircraft or network'},indent=2)+'\n')
    print('claude-design',json.dumps(result))
if __name__=='__main__':main()
