"""Native closed closeups of the actual corner-only derivative, unchanged PARKED pose."""
from pathlib import Path
import sys,json,hashlib,argparse
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
import blender_systems_review as R
from blender_loadout_review import CAMERAS,visibility_and_morph
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=ROOT/'qa/ramp-corner-candidate.glb'
fit=json.loads((ROOT/'qa/ramp-corner-fit-candidate.json').read_text())
assert sha(source)==fit['output']['sha256'] and fit['node_hierarchy_and_transforms_unchanged']
snapshots=json.loads((ROOT/'qa/viewer-poses-c130-family.json').read_text())
assert snapshots['model_sha256']==fit['input_sha256']
parked=next(s for s in snapshots['samples']if s['label']=='PARKED')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source))
objects=list(bpy.context.scene.objects);rest=R.capture_rest(objects)
args=argparse.Namespace(samples=12,resolution=1100,height_ratio=.70)
camera,lights,label=R.review_scene(args);renders=[]
for view in ['side','belly']:
 state=R.apply_snapshot(objects,rest,parked)
 R.configure_view(args,CAMERAS['ramp-'+view],objects,camera,lights,label,'C-130 / r0004 / final local cargo-corner candidate\nActual exported geometry / closed / '+view)
 visibility_and_morph(objects,parked);output=ROOT/'previews'/('ramp-corner-candidate-'+view+'.png');bpy.context.scene.render.filepath=str(output);bpy.ops.render.render(write_still=True)
 renders.append({'file':str(output.relative_to(ROOT)),'sha256':sha(output),'camera':CAMERAS['ramp-'+view],'pose':state})
report={'author':'claude-design','model_sha256':sha(source),'script_sha256':sha(__file__),'blender_version':bpy.app.version_string,'preserved_pose_basis':fit['input_sha256'],'scope':'Native closed derivative closeups; original PARKED world transforms are identical, geometry is actual candidate GLB. No substitute render meshes.','renders':renders}
(ROOT/'qa/ramp-corner-native.json').write_text(json.dumps(report,indent=2)+'\n')
