#!/usr/bin/env python3
"""claude-design | Bundle exact GLBs, articulation and pinned dependencies into one HTML.

No network is used. The resulting file opens directly without a local web server.
The normal folder viewer remains available for efficient Git-hosted use.
"""
from pathlib import Path
import base64, hashlib, json, re

ROOT=Path(__file__).resolve().parent
REV=ROOT.parent
def jsurl(source):
    return 'data:text/javascript;base64,'+base64.b64encode(source.encode()).decode()
def main():
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
    for key in ('c130','ac130','ac130j'):
        glb=(REV/'models'/f'{key}.glb').read_bytes()
        art=json.loads((REV/'articulation'/f'{key}.json').read_text())
        models[key]={'glb':base64.b64encode(glb).decode(),'articulation':art,'sha256':hashlib.sha256(glb).hexdigest()}
    html=(ROOT/'index.html').read_text()
    html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(ROOT/'style.css').read_text()+'</style>')
    html=re.sub(r'<script type="importmap">.*?</script>','<script type="importmap">'+json.dumps({'imports':imports},separators=(',',':'))+'</script>',html)
    notes=(REV/'REVISION.md').read_text() if (REV/'REVISION.md').exists() else (ROOT/'README.md').read_text()
    payload=json.dumps({'revision':'r0002','models':models,'notes':notes},separators=(',',':')).replace('</','<\\/')
    app=(ROOT/'app.mjs').read_text().replace('</script','<\\/script')
    html=html.replace('<script type="module" src="app.mjs"></script>','<script type="application/json" id="embedded-assets">'+payload+'</script>\n<script type="module">'+app+'</script>')
    dest=ROOT/'C130-family-portable.html'
    dest.write_text(html)
    info={'file':dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_models':{k:v['sha256'] for k,v in models.items()},'dependencies':'three 0.170.0; embedded, no network','runtime_render_validation':'NOT_RUN'}
    (ROOT/'portable-manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print('claude-design '+json.dumps(info))
if __name__=='__main__':main()
