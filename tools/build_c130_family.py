#!/usr/bin/env python3
"""Shared C-130 family: one original mesh, explicit variant kits, no overwrites.

R0001 is a DRAFT. This is not photo or native Unreal acceptance.
Original source GLBs remain immutable.
"""
import copy
import hashlib
import json
import math
import struct
from pathlib import Path

from audit_c130_glb import load_glb

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"family"/"r0001"
BASE=ROOT/"c130-hercules.glb"
EXPECTED="99a0dd53fa5e2359a191ac4a01699c189899a4777818c0a74a41c5272a410f2e"
# Original source is in model units, not metres. All three configurations
# share this identical conversion and identical original mesh accessors.
RAW_SPAN=3734.7827
RAW_LENGTH=2814.7672
RAW_HEIGHT=1078.5397
SCALE=[40.41/RAW_SPAN,29.79/RAW_LENGTH,11.84/RAW_HEIGHT]
SHIFT=[0.,-26.1702*SCALE[1],0.]
LEGACY_PROPS=[2,3,4,5]
PROPS=[
    (-494.43,-562.52,359.25),
    (-976.06,-562.52,359.25),
    (494.43,-562.52,359.25),
    (976.06,-562.52,359.25),
]
VARIANTS={
    "c130-hercules":{"designation":"C-130 legacy Hercules","prop":"legacy","kit":"none"},
    "ac130-hercules":{"designation":"AC-130 legacy gunship","prop":"legacy","kit":"legacy"},
    "ac130j-ghostrider":{"designation":"AC-130J Ghostrider candidate","prop":"j","kit":"ghostrider"},
}
SOCKETS={
    "SOCKET_PORT_30MM":[2.1,-2.3,2.7],
    "SOCKET_PORT_105MM":[2.1,3.1,2.7],
    "SOCKET_NOSE_EOIR":[0.,-12.1,3.0],
    "SOCKET_RECEIVER_UARRSI":[0.,-8.5,5.8],
    "SOCKET_TANKER_DELIVERY_PORT":[13.3,-5.1,5.1],
    "SOCKET_TANKER_DELIVERY_STARBOARD":[-13.3,-5.1,5.1],
    "SOCKET_FULTON_GAME_ONLY":[0.,-12.9,4.2],
    "SOCKET_JATO_GAME_ONLY_PORT":[2.2,2.5,1.6],
    "SOCKET_JATO_GAME_ONLY_STARBOARD":[-2.2,2.5,1.6],
}
def node(doc,name,children=None,**kwargs):
    item={"name":name}
    if children is not None:item["children"]=list(children)
    item.update(kwargs)
    doc["nodes"].append(item)
    return len(doc["nodes"])-1

def mat(doc,name,color):
    doc.setdefault("materials",[]).append({
        "name":name,
        "pbrMetallicRoughness":{"baseColorFactor":list(color),
                               "metallicFactor":0.15,"roughnessFactor":0.62},
        "doubleSided":True,
    })
    return len(doc["materials"])-1

def mesh(doc,binbuf,name,verts,faces,material,kind):
    if not verts or not faces:raise ValueError(name)
    def block(data,target):
        while len(binbuf)%4:binbuf.append(0)
        start=len(binbuf)
        binbuf.extend(data)
        doc["bufferViews"].append({"buffer":0,"byteOffset":start,
                                   "byteLength":len(data),"target":target})
        return len(doc["bufferViews"])-1
    vb=block(b"".join(struct.pack("<fff",*v) for v in verts),34962)
    flat=[i for face in faces for i in face]
    ib=block(b"".join(struct.pack("<I",i) for i in flat),34963)
    lo=[min(v[j] for v in verts) for j in range(3)]
    hi=[max(v[j] for v in verts) for j in range(3)]
    pa=len(doc["accessors"])
    doc["accessors"].append({"bufferView":vb,"componentType":5126,
        "count":len(verts),"type":"VEC3","min":lo,"max":hi})
    ia=len(doc["accessors"])
    doc["accessors"].append({"bufferView":ib,"componentType":5125,
        "count":len(flat),"type":"SCALAR","min":[min(flat)],"max":[max(flat)]})
    doc["meshes"].append({"name":name,"primitives":[{"attributes":{"POSITION":pa},
                     "indices":ia,"material":material,"mode":4}]})
    return node(doc,name,mesh=len(doc["meshes"])-1,
        extras={"level":1,"component_type":kind,
                "geometry_status":"ARTIST_APPROXIMATION_NOT_PHOTO_VERIFIED"})

def cylinder(axis,start,end,radius,segments=16):
    v=[];f=[]
    for center in (start,end):
        for i in range(segments):
            t=2*math.pi*i/segments
            a=radius*math.cos(t);b=radius*math.sin(t)
            if axis=="x":v.append((center[0],center[1]+a,center[2]+b))
            elif axis=="y":v.append((center[0]+a,center[1],center[2]+b))
            else:v.append((center[0]+a,center[1]+b,center[2]))
    for i in range(segments):
        j=(i+1)%segments
        f.extend(((i,j,segments+j),(i,segments+j,segments+i)))
    f.extend((tuple(range(segments-1,-1,-1)),
              tuple(range(segments,2*segments))))
    # Triangulate end caps for glTF TRIANGLES.
    triangles=[]
    for face in f:
        for j in range(1,len(face)-1):
            triangles.append((face[0],face[j],face[j+1]))
    return v,triangles

def sphere(center,radius,stacks=8,sectors=16):
    v=[];f=[]
    for i in range(stacks+1):
        theta=math.pi*i/stacks
        for j in range(sectors):
            phi=2*math.pi*j/sectors
            v.append((center[0]+radius*math.sin(theta)*math.cos(phi),
                      center[1]+radius*math.sin(theta)*math.sin(phi),
                      center[2]+radius*math.cos(theta)))
    for i in range(stacks):
        for j in range(sectors):
            a=i*sectors+j;b=i*sectors+(j+1)%sectors
            c=(i+1)*sectors+j;d=(i+1)*sectors+(j+1)%sectors
            f.extend(((a,c,d),(a,d,b)))
    return v,f

def add_barrel(doc,buf,name,position,length,radius,matid):
    x,y,z=position
    a,b=cylinder("x",(x,y,z),(x+length,y,z),radius)
    return mesh(doc,buf,name,a,b,matid,"gun_barrel")

def add_six_blade(doc,buf,prop_id,center,matid):
    cx,cy,cz=center
    verts=[];faces=[]
    # Six scimitar-style blades, six radial roots, swept outer tips.
    for k in range(6):
        a=2*math.pi*k/6
        start=len(verts)
        for r,width,sweep,twist in ((.26,.20,0.,-.06),
                                    (.65,.24,.07,.03),
                                    (1.22,.22,.14,.08),
                                    (1.75,.14,.21,.10),
                                    (2.04,.045,.27,.08)):
            dx=math.cos(a)*r-math.sin(a)*sweep
            dz=math.sin(a)*r+math.cos(a)*sweep
            px=-math.sin(a);pz=math.cos(a)
            verts.extend([(cx+dx+px*width/2,cy+twist,cz+dz+pz*width/2),
                          (cx+dx-px*width/2,cy-twist,cz+dz-pz*width/2)])
        for j in range(4):
            p=start+j*2
            faces.extend(((p,p+1,p+3),(p,p+3,p+2)))
    return mesh(doc,buf,"PROP6_BLADES_"+str(prop_id),verts,faces,matid,"six_blade_propeller")
