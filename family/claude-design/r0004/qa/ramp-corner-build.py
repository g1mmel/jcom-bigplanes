"""Build a corner-only derivative of the frozen master and prove rig/deck identity."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
from ramp_repair import _read,_array,repair_ramp_corners_glb
from gltf_core import GLB
from family_glb import compact

def clip_digest(d,b):
 records=[]
 for a in d['animations']:
  for c in a['channels']:
   s=a['samplers'][c['sampler']];records.append([a['name'],d['nodes'][c['target']['node']]['name'],c['target']['path'],s.get('interpolation','LINEAR'),_array(d,b,s['input']).tolist(),_array(d,b,s['output']).tolist()])
 return hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()

def mesh_digest(d,b,name):
 n=next(n for n in d['nodes']if n['name']==name);h=hashlib.sha256()
 for p in d['meshes'][n['mesh']]['primitives']:
  for k,a in sorted(p['attributes'].items()):h.update(k.encode());h.update(_array(d,b,a).tobytes())
  h.update(_array(d,b,p['indices']).tobytes())
 return h.hexdigest()

def hierarchy(d):
 return json.dumps([{k:n[k]for k in ['name','children','translation','rotation','scale','matrix']if k in n}for n in d['nodes']],sort_keys=True)

def main():
 D,B,S=_read(ROOT/'models/c130-family.glb');clips=clip_digest(D,B);deck=mesh_digest(D,B,'CARGO_RAMP_INTERIOR_PRESERVED');transforms=hierarchy(D)
 report=repair_ramp_corners_glb(D,B);report.update(input_sha256=S,clips_unchanged=clips==clip_digest(D,B),cargo_deck_unchanged=deck==mesh_digest(D,B,'CARGO_RAMP_INTERIOR_PRESERVED'),node_hierarchy_and_transforms_unchanged=transforms==hierarchy(D))
 assert report['clips_unchanged'] and report['cargo_deck_unchanged'] and report['node_hierarchy_and_transforms_unchanged']
 g=GLB('ramp-corner-candidate');g.doc=D;g.buf=B;compact(g);result=g.write(ROOT/'qa/ramp-corner-candidate.glb');report['output']=result
 (ROOT/'qa/ramp-corner-fit-candidate.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'output':result,'preservation':{k:report[k]for k in ['clips_unchanged','cargo_deck_unchanged','node_hierarchy_and_transforms_unchanged']},'before':{k:v['maximum']['distance_m']for k,v in report['before']['sides'].items()},'after':{k:v['maximum']['distance_m']for k,v in report['after']['sides'].items()},'lip_after':[(r['side'],r['abs_x_m'],r['distance_m'])for r in report['after']['aft_lip_samples']],'changes':report['changes']},indent=2),flush=True)
if __name__=='__main__':main()
