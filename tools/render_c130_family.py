#!/usr/bin/env python3
"""Software-raster orthographic previews of the generated C-130 candidate GLBs.

No GPU, Blender or Unreal. Neutral flat shading, not photographic validation.
Requires Pillow only; original textures are not represented in these images.
"""
import math
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from audit_c130_glb import load_glb, world_nodes, transform

ROOT=Path(__file__).resolve().parents[1]
FAMILY=ROOT/"family"/"r0001"
OUT=FAMILY/"previews"
OUT.mkdir(parents=True,exist_ok=True)
VIEWS={
    "side":((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)),
    "front":((0.,-1.,0.),(1.,0.,0.),(0.,0.,1.)),
    "top":((0.,0.,1.),(0.,1.,0.),(-1.,0.,0.)),
}
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a):
    length=math.sqrt(dot(a,a))
    return tuple(x/length for x in a)
camera=unit((1.,-1.25,.8))
right=unit(cross((0.,0.,1.),camera))
up=unit(cross(camera,right))
VIEWS["hero"]=(camera,right,up)

def accessible(doc):
    nodes=doc["nodes"]
    roots=doc["scenes"][doc.get("scene",0)]["nodes"]
    seen=set()
    def visit(i):
        if i in seen:return
        seen.add(i)
        for c in nodes[i].get("children",[]):visit(c)
    for root in roots:visit(root)
    return seen

def read_indices(doc,binary,accid):
    a=doc["accessors"][accid]
    v=doc["bufferViews"][a["bufferView"]]
    types={5121:"B",5123:"H",5125:"I"}
    fmt=types[a["componentType"]]
    stride=v.get("byteStride",struct.calcsize(fmt))
    start=v.get("byteOffset",0)+a.get("byteOffset",0)
    return [struct.unpack_from("<"+fmt,binary,start+i*stride)[0]
            for i in range(a["count"])]

def read_positions(doc,binary,accid):
    a=doc["accessors"][accid]
    v=doc["bufferViews"][a["bufferView"]]
    stride=v.get("byteStride",12)
    start=v.get("byteOffset",0)+a.get("byteOffset",0)
    return [struct.unpack_from("<fff",binary,start+i*stride)
            for i in range(a["count"])]

def triangles(path):
    raw,doc,binary=load_glb(path)
    world=world_nodes(doc)
    used=accessible(doc)
    result=[]
    for i,n in enumerate(doc["nodes"]):
        if i not in used or "mesh" not in n:continue
        name=n.get("name","")
        if "Interior_" in name or "HydrolicInterior" in name:continue
        mesh=doc["meshes"][n["mesh"]]
        for prim in mesh["primitives"]:
            if prim.get("mode",4)!=4 or "POSITION" not in prim["attributes"]:continue
            verts=[transform(world[i],p) for p in read_positions(doc,binary,prim["attributes"]["POSITION"])]
            indices=read_indices(doc,binary,prim["indices"]) if "indices" in prim else list(range(len(verts)))
            category=("glass" if "window" in name.lower() else
                      "prop" if "prop" in name.lower() else
                      "gear" if "wheel" in name.lower() or "gear" in name.lower() else
                      "kit" if "PROXY" in name or "BLADES" in name else "body")
            for j in range(0,len(indices)-2,3):
                p,q,r=(verts[indices[j]],verts[indices[j+1]],verts[indices[j+2]])
                result.append((p,q,r,category))
    return result

def render(tris,title,view,width=1200,height=720):
    forward,axis_x,axis_y=view
    projected=[]
    lo=[float("inf")]*2
    hi=[float("-inf")]*2
    for p,q,r,category in tris:
        xyz=(p,q,r)
        xy=[(dot(v,axis_x),dot(v,axis_y)) for v in xyz]
        for x,y in xy:
            lo[0]=min(lo[0],x);lo[1]=min(lo[1],y)
            hi[0]=max(hi[0],x);hi[1]=max(hi[1],y)
        depth=sum(dot(v,forward) for v in xyz)/3
        u=tuple(q[i]-p[i] for i in range(3))
        v=tuple(r[i]-p[i] for i in range(3))
        normal=unit(cross(u,v)) if dot(cross(u,v),cross(u,v))>1e-16 else (0,0,1)
        light=max(.15,min(1.,.48+.42*abs(dot(normal,unit((.6,-.35,.7))))))
        projected.append((depth,xy,category,light))
    scale=min((width-110)/max(.001,hi[0]-lo[0]),
              (height-130)/max(.001,hi[1]-lo[1]))
    center=((lo[0]+hi[0])/2,(lo[1]+hi[1])/2)
    image=Image.new("RGB",(width,height),(10,22,34))
    draw=ImageDraw.Draw(image)
    for x in range(0,width,60):draw.line((x,0,x,height),fill=(24,39,53))
    for y in range(0,height,60):draw.line((0,y,width,y),fill=(24,39,53))
    palette={"body":(170,180,185),"glass":(56,112,144),
             "prop":(44,49,54),"gear":(66,73,78),"kit":(80,89,99)}
    for depth,xy,category,light in sorted(projected,key=lambda v:v[0]):
        coords=[(int(width/2+(x-center[0])*scale),
                 int(height/2-(y-center[1])*scale)) for x,y in xy]
        c=palette[category]
        color=tuple(int(max(0,min(255,v*light))) for v in c)
        draw.polygon(coords,fill=color)
    draw.rectangle((0,0,width,45),fill=(9,17,26))
    draw.text((20,14),title,fill=(225,232,236))
    draw.text((20,height-27),"cg11 r0001  |  SINGLE SOURCE AIRFRAME  |  DRAFT / NOT PHOTO ACCEPTED",
              fill=(245,173,106))
    return image

def main():
    paths={
        "C130":FAMILY/"c130-hercules-unified-r0001.glb",
        "AC130":FAMILY/"ac130-hercules-unified-r0001.glb",
        "AC130J":FAMILY/"ac130j-ghostrider-unified-r0001.glb",
    }
    previews=[]
    for name,path in paths.items():
        tri=triangles(path)
        print(name,"visible triangles",len(tri))
        for label,view in VIEWS.items():
            img=render(tri,name+" unified r0001 — "+label.upper(),view)
            file=OUT/(name.lower()+"-"+label+".png")
            img.save(file)
            previews.append(file)
            print("PREVIEW",file.name,file.stat().st_size)
    sheet=Image.new("RGB",(2400,1440),(9,17,26))
    for j,label in enumerate(("side","front","top","hero")):
        file=OUT/("ac130j-"+label+".png")
        sheet.paste(Image.open(file),((j%2)*1200,(j//2)*720))
    sheet.save(OUT/"ac130j-contact-sheet.png")
    print("DRAFT renders complete; no photographic comparison has been done.")

if __name__=="__main__":
    main()
