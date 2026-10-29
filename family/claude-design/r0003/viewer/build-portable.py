#!/usr/bin/env python3
"""claude-design | Bundle exact GLBs, articulation and pinned dependencies into one HTML.

No network is used. The resulting file opens directly without a local web server.
The normal folder viewer remains available for efficient Git-hosted use.
"""
from pathlib import Path
import argparse, base64, gzip, hashlib, json, re

ROOT=Path(__file__).resolve().parent
REV=ROOT.parent
def jsurl(source):
    return 'data:text/javascript;base64,'+base64.b64encode(source.encode()).decode()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--component',choices=['gau23-visual','m102-airborne-visual','eoir-visual'])
    parser.add_argument('--aircraft-only',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    modules={
        'three':'vendor/three.module.js',
        'c130-controller':'controller.mjs',
        'c130-pose-driver':'pose-driver.mjs',
        'gltf-loader':'vendor/GLTFLoader.js',
        'orbit-controls':'vendor/OrbitControls.js',
        'c130-buffer-utils':'vendor/BufferGeometryUtils.js',
    }
    imports={}
    for name,path in modules.items():
        source=(ROOT/path).read_text()
        if name=='gltf-loader':source=source.replace("'./BufferGeometryUtils.js'","'c130-buffer-utils'")
        imports[name]=jsurl(source)
    models={}
    aircraft=['c130','ac130','ac130j']
    components=['gau23-visual','m102-airborne-visual','eoir-visual']
    keys=[args.component] if args.component else aircraft if args.aircraft_only else aircraft+components
    for key in keys:
        component=key in components
        glb_path=REV/'components'/key/'model.glb' if component else REV/'models'/f'{key}.glb'
        art_path=REV/'components'/key/'articulation.json' if component else REV/'articulation'/f'{key}.json'
        glb=glb_path.read_bytes()
        art=json.loads(art_path.read_text())
        packed=gzip.compress(glb,compresslevel=9,mtime=0)
        assert gzip.decompress(packed)==glb
        models[key]={'glb':base64.b64encode(packed).decode(),'encoding':'gzip+base64','articulation':art,'sha256':hashlib.sha256(glb).hexdigest(),'source':str(glb_path.relative_to(REV))}
    html=(ROOT/'index.html').read_text()
    html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(ROOT/'style.css').read_text()+'</style>')
    html=re.sub(r'<script type="importmap">.*?</script>','<script type="importmap">'+json.dumps({'imports':imports},separators=(',',':'))+'</script>',html)
    notes=(REV/'REVISION.md').read_text() if (REV/'REVISION.md').exists() else (ROOT/'README.md').read_text()
    reference_notes=REV/'references'/'REFERENCE_NOTES.md'
    if reference_notes.exists():notes+='\n\n---\n\n'+reference_notes.read_text()
    payload=json.dumps({'revision':'r0003','models':models,'default_asset':args.component or 'ac130j','notes':notes},separators=(',',':')).replace('</','<\\/')
    app=(ROOT/'app.mjs').read_text().replace('</script','<\\/script')
    html=html.replace('<script type="module" src="app.mjs"></script>','<script type="application/json" id="embedded-assets">'+payload+'</script>\n<script type="module">'+app+'</script>')
    dest=args.output or ROOT/((args.component+'-portable.html') if args.component else 'C130-family-portable.html')
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(html)
    info={'file':dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_models':{k:v['sha256'] for k,v in models.items()},'dependencies':'three 0.170.0; embedded, no network; browser DecompressionStream gzip','runtime_render_validation':'NOT_RUN'}
    (dest.with_suffix('.manifest.json') if args.component or args.output else ROOT/'portable-manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print('claude-design '+json.dumps(info))
if __name__=='__main__':main()
