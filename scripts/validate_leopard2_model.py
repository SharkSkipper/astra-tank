"""Reopen the deliverable and verify real geometry, editable parts, and pivot behavior."""

import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'models'/'leopard2'
checks = []


def check(name, ok, detail=None):
    checks.append({'check':name,'pass':bool(ok),'detail':detail})


def world_vertex(obj, index=0):
    return obj.matrix_world @ obj.data.vertices[index].co


def update():
    for name in ('Turret_Pivot','Gun_Elevation_Pivot'):
        bpy.data.objects[name].update_tag()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current+1)
    bpy.context.view_layer.update()


scene=bpy.context.scene
model=bpy.data.collections['LEOPARD 2 | Editable exterior']
objects=list(model.all_objects)
meshes=[o for o in objects if o.type=='MESH']
check('Meters and Z-up scene',scene.unit_settings.system=='METRIC' and scene.unit_settings.scale_length==1)
check('Separate editable exterior meshes',len(meshes)>1500,len(meshes))
check('Packed original reference',any(im.packed_file for im in bpy.data.images))
check('Embedded editing instructions','00_README_MODEL' in bpy.data.texts)
check('Live editable bevel modifiers',sum(m.type=='BEVEL' for o in objects for m in o.modifiers)>500)

depsgraph=bpy.context.evaluated_depsgraph_get()
mins=[math.inf]*3;maxs=[-math.inf]*3
nonfinite=[];empty=[];vertices=0;triangles=0
for obj in objects:
    if obj.type not in ('MESH','CURVE'):
        continue
    evaluated=obj.evaluated_get(depsgraph)
    data=evaluated.to_mesh()
    if not data.vertices:
        empty.append(obj.name)
    for vertex in data.vertices:
        p=evaluated.matrix_world@vertex.co
        if not all(math.isfinite(v) for v in p):
            nonfinite.append(obj.name)
        for i in range(3):
            mins[i]=min(mins[i],p[i]);maxs[i]=max(maxs[i],p[i])
    vertices+=len(data.vertices)
    data.calc_loop_triangles();triangles+=len(data.loop_triangles)
    evaluated.to_mesh_clear()
dimensions=[maxs[i]-mins[i] for i in range(3)]
check('Finite nonempty geometry',not nonfinite and not empty,{'nonfinite':nonfinite,'empty':empty})
check('Overall length within 5 mm of 9.613 m',abs(dimensions[0]-9.613)<.005,dimensions[0])
check('Overall width within 2 mm of 3.700 m',abs(dimensions[1]-3.700)<.002,dimensions[1])
check('Track pads grounded; no stray components below ground',-.002<mins[2]<.002,mins[2])

for side,sign in [('L',1),('R',-1)]:
    stations=[o for o in objects if o.name.startswith(side+'_RoadWheel_Station_')]
    tires=[o for o in objects if o.name.startswith(side+'_RoadWheel_') and o.name.endswith('_RubberTire')]
    links=[o for o in objects if o.name.startswith(side+'_TrackLink_')]
    check(side+' seven paired wheel stations',len(stations)==7 and len(tires)==14,{'stations':len(stations),'tires':len(tires)})
    check(side+' 85 individually named linked shoes',len(links)==85 and len({o.data.name for o in links})==1)
    check(side+' 1.3925 m track center',all(abs(o.matrix_world.translation.y-sign*1.3925)<1e-5 for o in links))
    check(side+' correct first road wheel origin',
          (bpy.data.objects[side+'_RoadWheel_Station_01'].matrix_world.translation-Vector((-1.90,sign*1.3925,.46))).length<1e-5)

turret=bpy.data.objects['Turret_Pivot']
gun=bpy.data.objects['Gun_Elevation_Pivot']
barrel=bpy.data.objects['Gun_ExternalTube_HollowMuzzle']
roof=bpy.data.objects['Primary_Sight_Housing']
hull=bpy.data.objects['Hull_Main_WeldedShell']
check('Turret pivot on race axis',(turret.matrix_world.translation-Vector((0,0,1.675))).length<1e-5)
check('Gun pivot at 2.009 m above ground',(gun.matrix_world.translation-Vector((-1.26,0,2.009))).length<1e-5)
check('Driver curves valid',all(f.is_valid for o in (turret,gun) for f in o.animation_data.drivers))
base_barrel=world_vertex(barrel);base_roof=world_vertex(roof);base_hull=world_vertex(hull)
pivot=turret.matrix_world.translation.copy()
turret['yaw_degrees']=32;update()
expected=pivot+Matrix.Rotation(math.radians(32),3,'Z')@(base_barrel-pivot)
check('Turret yaw moves gun correctly',(world_vertex(barrel)-expected).length<1e-4)
expected=pivot+Matrix.Rotation(math.radians(32),3,'Z')@(base_roof-pivot)
check('Turret yaw carries roof fittings',(world_vertex(roof)-expected).length<1e-4)
check('Turret yaw leaves hull fixed',(world_vertex(hull)-base_hull).length<1e-6)
turret['yaw_degrees']=0;update()
gun['elevation_degrees']=12;update()
pivot=Vector((-1.26,0,2.009))
expected=pivot+Matrix.Rotation(math.radians(12),3,'Y')@(base_barrel-pivot)
check('Gun elevation uses mantlet pivot',(world_vertex(barrel)-expected).length<1e-4)
check('Gun elevation leaves sight and turret fixed',(world_vertex(roof)-base_roof).length<1e-6)
gun['elevation_degrees']=0;update()
check('Neutral pose restores exact baseline',(world_vertex(barrel)-base_barrel).length<1e-5)

with (OUT/'Leopard_2_early_prototype.glb').open('rb') as f:
    magic,version,length=struct.unpack('<4sII',f.read(12))
    size,kind=struct.unpack('<I4s',f.read(8))
    gltf=json.loads(f.read(size))
check('Valid GLB 2 container',magic==b'glTF' and version==2 and kind==b'JSON')
check('GLB excludes studio and reference',not any(n.get('name','').startswith(('Studio_','Camera_','Reference_')) for n in gltf['nodes']))
check('GLB contains model hierarchy and separate parts',len(gltf['nodes'])>1500,len(gltf['nodes']))

report={'passed':all(c['pass'] for c in checks),'checks':checks,
        'evaluated_bbox_m':{'min':mins,'max':maxs,'dimensions':dimensions},
        'model_objects':len(objects),'mesh_objects':len(meshes),
        'evaluated_vertices_counting_instances':vertices,
        'evaluated_triangles_counting_instances':triangles,
        'file':str(bpy.data.filepath),'blender_version':bpy.app.version_string}
(OUT/'validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
if not report['passed']:
    raise RuntimeError('Model validation failed. See validation_report.json')
