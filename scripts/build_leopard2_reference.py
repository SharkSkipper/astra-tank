"""Build an editable exterior model from the user's early Leopard 2 four-view scan."""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tank_common import box, collection, cyl, empty, loft, material, mesh, prism, rod, torus, tube
from tank_running_gear import build_running_gear

OUT = ROOT / 'models' / 'leopard2'
PREVIEW = ROOT / 'assets' / 'leopard2'
OUT.mkdir(parents=True, exist_ok=True)
PREVIEW.mkdir(parents=True, exist_ok=True)


def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    scene.unit_settings.length_unit = 'METERS'
    return scene


def make_materials():
    return {
        'olive': material('Paint | muted NATO olive', (.135,.173,.094), .28,.43,True),
        'olive_dark': material('Paint | recess and brackets', (.072,.092,.047), .32,.5,True),
        'olive_light': material('Paint | edge fittings', (.185,.218,.132), .35,.44),
        'steel': material('Steel | track contact edges', (.28,.29,.25), .8,.37),
        'steel_dark': material('Steel | dark forged', (.065,.073,.067), .7,.46),
        'rubber': material('Rubber | tire and track pads', (.025,.031,.028), .02,.76,True),
        'bolt': material('Fasteners | aged phosphated steel', (.19,.211,.16), .67,.4),
        'black': material('Deep mechanical cavities', (.012,.016,.014), .05,.75),
        'glass': material('Optical glass', (.035,.145,.19), .65,.16),
        'lamp': material('Headlight glass', (.72,.78,.65), .3,.15),
        'red': material('Tail lamp lens', (.40,.018,.008), .15,.25),
        'white': material('Registration paint', (.77,.80,.71), .05,.66),
    }


def bolt(name, p, col, parent, axis=(0,0,1), radius=.011):
    return cyl(name,p,radius,.012,M['bolt'],col,parent,axis,6,.001)


def handle(name, x, y, z, col, parent, width=.16, axis='X'):
    if axis == 'X':
        pts=[(x-width/2,y,z),(x-width/2,y,z+.04),(x+width/2,y,z+.04),(x+width/2,y,z)]
    else:
        pts=[(x,y-width/2,z),(x,y-width/2,z+.04),(x,y+width/2,z+.04),(x,y+width/2,z)]
    return tube(name,pts,.011,M['olive_dark'],col,parent)


def panel_bolts(name, xmin, xmax, ymin, ymax, z, col, parent, nx=5):
    for y in (ymin,ymax):
        for i in range(nx):
            x=xmin+(xmax-xmin)*i/(nx-1)
            bolt(f'{name}_{y:+.2f}_{i:02d}',(x,y,z),col,parent)


def build_hull():
    c=collection('01 | Hull armor and welded body',MODEL)
    # The bow is a sloped prism with a raised deck; the underside clears the ground.
    rings=[]
    for x,half,zbase,ztop in [(-3.20,1.35,.80,1.19),(-2.26,1.41,.55,1.54),
                              (2.85,1.39,.50,1.57),(4.30,1.31,.66,1.57)]:
        rings.append([(x,-half+.20,zbase),(x,half-.20,zbase),
                      (x,half,ztop-.12),(x,half,ztop),
                      (x,-half,ztop),(x,-half,ztop-.12)])
    hull=loft('Hull_Main_WeldedShell',rings,M['olive'],c,ROOT_OBJ,.016)
    hull['reference']='User scan; 7.672 m fender envelope, estimated hidden underside'
    box('Lower_Belly_Plate',(.78,0,.545),(5.82,2.20,.08),M['olive_dark'],c,ROOT_OBJ,.016)
    cyl('Turret_Race_Lower',(0,0,1.615),1.13,.10,M['steel_dark'],c,ROOT_OBJ,vertices=96)
    cyl('Turret_Race_Upper',(0,0,1.674),1.09,.065,M['olive_dark'],c,ROOT_OBJ,vertices=96)
    for s in (-1,1):
        side='L' if s>0 else 'R'
        # Fender outer edge establishes the drawing's 3.700 m maximum width.
        poly=[(-3.272,s*1.38),(-3.13,s*1.85),(4.28,s*1.85),(4.395,s*1.63),(4.395,s*1.32)]
        prism(f'{side}_FullLength_Fender',poly,1.385,1.455,M['olive'],c,ROOT_OBJ,.012)
        tube(f'{side}_Fender_Outer_Seam',[(-3.12,s*1.823,1.461),(4.23,s*1.823,1.461),
                                             (4.36,s*1.62,1.461)],.012,M['olive_light'],c,ROOT_OBJ)
        front=[(-3.265,s*1.49,.91),(-3.265,s*1.84,1.03),(-3.265,s*1.84,1.40),(-3.265,s*1.39,1.40)]
        back=[(x+.05,y,z) for x,y,z in front]
        loft(f'{side}_Front_Mudguard',[front,back],M['olive'],c,ROOT_OBJ,.01)
        box(f'{side}_Rear_RubberFlap',(4.335,s*1.46,.89),(.05,.56,.74),M['rubber'],c,ROOT_OBJ,.008)
        box(f'{side}_Rear_FlapClamp',(4.366,s*1.46,1.20),(.035,.58,.055),M['olive'],c,ROOT_OBJ)
        for y in (-.20,0,.20):
            bolt(f'{side}_FlapBolt_{y}',(4.389,s*1.46+y,1.20),c,ROOT_OBJ,(1,0,0))
        for i,(xa,xb) in enumerate([(-3.08,-2.44),(-2.42,-1.60),(-1.58,-.70),
                                   (-.68,.22),(.24,1.13),(1.15,2.04),(2.06,2.96),(2.98,3.63)]):
            low=.94 if i<7 else 1.09
            rings=[[(xa,s*1.785,low),(xb,s*1.785,low),(xb,s*1.785,1.398),(xa,s*1.785,1.398)],
                   [(xa,s*1.809,low),(xb,s*1.809,low),(xb,s*1.809,1.398),(xa,s*1.809,1.398)]]
            loft(f'{side}_Skirt_Panel_{i+1:02d}',rings,M['olive'],c,ROOT_OBJ,.006)
            for x in (xa+.065,xb-.065):
                box(f'{side}_Skirt_Hinge_{i}_{x:.2f}',(x,s*1.824,1.409),(.065,.035,.08),M['olive_dark'],c,ROOT_OBJ)
                bolt(f'{side}_Skirt_Bolt_{i}_{x:.2f}',(x,s*1.842,1.397),c,ROOT_OBJ,(0,s,0))
        for i in range(5):
            x=-1.43+i*.91
            box(f'{side}_Fender_Stowage_{i+1}',(x,s*1.59,1.525),(.865,.375,.145),M['olive'],c,ROOT_OBJ,.014)
            box(f'{side}_Stowage_Lid_{i+1}',(x,s*1.59,1.605),(.855,.365,.025),M['olive_light'],c,ROOT_OBJ,.005)
            for xx in (x-.26,x+.26):
                box(f'{side}_Stowage_Clasp_{i}_{xx:.2f}',(xx,s*1.79,1.541),(.053,.027,.075),M['steel_dark'],c,ROOT_OBJ)
    return hull


def build_hull_fittings():
    c=collection('02 | Deck fans grilles tools and towing',MODEL)
    # Two large rear fans: visible blades underneath physically open crossed grilles.
    for s in (-1,1):
        side='L' if s>0 else 'R'
        x,y,z=3.57,s*.67,1.596
        cyl(f'{side}_Fan_Recess',(x,y,z),.602,.038,M['black'],c,ROOT_OBJ,vertices=80)
        cyl(f'{side}_Fan_Hub',(x,y,z+.024),.107,.049,M['steel_dark'],c,ROOT_OBJ)
        for i in range(12):
            a=i*math.tau/12
            pts=[]
            for radius,angle in [(.12,a),(.52,a+.18),(.54,a+.47),(.19,a+.34)]:
                pts.append((x+radius*math.cos(angle),y+radius*math.sin(angle)))
            prism(f'{side}_Fan_Blade_{i:02d}',pts,z+.016,z+.034,M['steel_dark'],c,ROOT_OBJ,.001)
        for radius in (.58,.603):
            torus(f'{side}_Fan_Rim_{radius}',(x,y,z+.068),radius,.013,M['olive_light'],c,ROOT_OBJ)
        for j in range(-13,14):
            offset=j*.04
            span=math.sqrt(max(.564**2-offset**2,0))
            rod(f'{side}_Fan_GridX_{j}',(x-span,y+offset,z+.064),(x+span,y+offset,z+.064),.0045,M['steel_dark'],c,ROOT_OBJ)
            rod(f'{side}_Fan_GridY_{j}',(x+offset,y-span,z+.071),(x+offset,y+span,z+.071),.0045,M['steel_dark'],c,ROOT_OBJ)
        for i in range(12):
            a=math.tau*i/12
            bolt(f'{side}_Fan_RimBolt_{i}',(x+.602*math.cos(a),y+.602*math.sin(a),z+.078),c,ROOT_OBJ)
        box(f'{side}_Engine_Louvre_Recess',(2.67,s*.70,1.608),(.50,1.01,.025),M['black'],c,ROOT_OBJ)
        for i in range(14):
            box(f'{side}_Engine_Louvre_{i:02d}',(2.44+i*.0354,s*.70,1.638),(.015,.96,.034),M['olive_dark'],c,ROOT_OBJ,.002)
        # Long cable loops follow the fender top, with collars and eyes.
        pts=[(-1.03,s*1.42,1.66),(-1.48,s*1.47,1.635),(-2.19,s*1.51,1.58),
             (-2.36,s*1.64,1.535),(-1.98,s*1.69,1.64),(.9,s*1.71,1.65),
             (2.58,s*1.71,1.65),(3.85,s*1.67,1.63),(4.06,s*1.51,1.63)]
        tube(f'{side}_TowCable_Main',pts,.026,M['steel_dark'],c,ROOT_OBJ)
        for x in (-1.35,.80,2.65):
            box(f'{side}_Cable_Clamp_{x}',(x,s*1.71,1.65),(.10,.085,.05),M['olive_dark'],c,ROOT_OBJ)
        for xx,yy,zz in (pts[0],pts[-1]):
            torus(f'{side}_Cable_Eye_{xx}',(xx,yy,zz),.068,.020,M['steel_dark'],c,ROOT_OBJ)
        rod(f'{side}_PioneerTool_Shaft',(2.35,s*1.47,1.681),(3.61,s*1.47,1.681),.022,M['olive_light'],c,ROOT_OBJ)
        box(f'{side}_PioneerTool_Head',(3.71,s*1.47,1.68),(.28,.17,.035),M['steel_dark'],c,ROOT_OBJ,.022)
        # Front headlights in cages, and towing shackles.
        cyl(f'{side}_Headlight_Housing',(-3.077,s*1.43,1.471),.093,.10,M['olive_dark'],c,ROOT_OBJ,(-1,0,0))
        cyl(f'{side}_Headlight_Lens',(-3.133,s*1.43,1.471),.074,.008,M['lamp'],c,ROOT_OBJ,(-1,0,0))
        torus(f'{side}_Headlight_Bezel',(-3.14,s*1.43,1.471),.082,.010,M['olive'],c,ROOT_OBJ,(-1,0,0))
        tube(f'{side}_Headlight_Guard',[(-3.17,s*1.31,1.37),(-3.17,s*1.31,1.59),
             (-3.17,s*1.55,1.59),(-3.17,s*1.55,1.37)],.012,M['olive_dark'],c,ROOT_OBJ)
        for x in (-3.16,4.335):
            box(f'{side}_Tow_Lug_{x}',(x,s*1.11,1.08),(.115,.135,.21),M['olive_dark'],c,ROOT_OBJ,.025)
            torus(f'{side}_Tow_Shackle_{x}',(-3.125 if x<0 else 4.266,s*1.11,1.04),.103,.026,M['steel_dark'],c,ROOT_OBJ,(0,1,0))
        cyl(f'{side}_Rear_TailLamp',(4.324,s*1.15,1.315),.052,.028,M['red'],c,ROOT_OBJ,(1,0,0))
        # Rear exhaust outlet with inset louvers.
        box(f'{side}_Rear_Exhaust_Recess',(4.31,s*.69,1.315),(.044,.88,.32),M['black'],c,ROOT_OBJ)
        for i in range(8):
            box(f'{side}_Rear_Exhaust_Louvre_{i}',(4.345,s*.69,1.18+i*.038),(.048,.86,.018),M['olive_dark'],c,ROOT_OBJ,.002)
    box('Rear_Engine_Deck_Separator',(3.64,0,1.62),(1.30,.06,.037),M['olive'],c,ROOT_OBJ)
    box('Rear_Service_Access_Hatch',(4.30,0,.982),(.055,1.22,.36),M['olive'],c,ROOT_OBJ,.018)
    handle('Rear_Service_Handle',4.34,0,1.06,c,ROOT_OBJ,axis='Y')
    box('Bow_Center_AccessPlate',(-2.49,0,1.472),(.45,.66,.026),M['olive_dark'],c,ROOT_OBJ)
    for y in (-.40,.40):
        for x in (-2.75,-2.48,-2.21):
            box(f'Bow_SpareTrack_Block_{x}_{y}',(x,y,1.463),(.19,.30,.065),M['steel_dark'],c,ROOT_OBJ)
            box(f'Bow_SpareTrack_Pad_{x}_{y}',(x,y,1.502),(.15,.25,.025),M['rubber'],c,ROOT_OBJ)
    # Driver's hatch sits on the right forward shoulder.
    poly=[(-2.13,.40),(-1.62,.40),(-1.45,.70),(-1.64,1.10),(-2.19,1.02)]
    prism('Driver_Hatch_Seal',poly,1.549,1.573,M['rubber'],c,ROOT_OBJ)
    prism('Driver_Hatch_Lid',[(x*.993,y*.993) for x,y in poly],1.572,1.62,M['olive'],c,ROOT_OBJ)
    handle('Driver_Hatch_Handle',-1.91,.82,1.623,c,ROOT_OBJ)
    for i in range(3):
        box(f'Driver_Periscope_{i}',(-2.06,.47+i*.18,1.665),(.13,.14,.095),M['olive_dark'],c,ROOT_OBJ)
        box(f'Driver_Periscope_Glass_{i}',(-2.132,.47+i*.18,1.669),(.007,.103,.045),M['glass'],c,ROOT_OBJ)


def build_turret():
    c=collection('04 | Turret shell and mantlet',MODEL)
    global TURRET, GUN
    TURRET=empty('Turret_Pivot',c,(0,0,1.675),ROOT_OBJ)
    TURRET['yaw_degrees']=0.0
    TURRET.id_properties_ui('yaw_degrees').update(min=-180,max=180,description='Turret yaw in degrees; rotates all turret components')
    d=TURRET.driver_add('rotation_euler',2).driver
    v=d.variables.new();v.name='yaw';v.targets[0].id=TURRET;v.targets[0].data_path='["yaw_degrees"]'
    d.expression='yaw*pi/180'
    lower=[(-1.57,-.65,1.742),(-1.43,-1.03,1.718),(-.92,-1.32,1.718),
           (1.42,-1.36,1.718),(2.91,-1.10,1.792),(3.036,-.90,1.82),
           (3.036,.90,1.82),(2.91,1.10,1.792),(1.42,1.36,1.718),
           (-.92,1.32,1.718),(-1.43,1.03,1.718),(-1.57,.65,1.742)]
    upper=[(-1.43,-.59,2.43),(-1.23,-.91,2.46),(-.82,-1.13,2.49),
           (1.39,-1.18,2.513),(2.81,-.98,2.445),(2.93,-.82,2.405),
           (2.93,.82,2.405),(2.81,.98,2.445),(1.39,1.18,2.513),
           (-.82,1.13,2.49),(-1.23,.91,2.46),(-1.43,.59,2.43)]
    shell=loft('Turret_Main_WeldedShell',[lower,upper],M['olive'],c,TURRET,.012)
    shell['identification']='Early Leopard 2 prototype family; exact PT/T number unconfirmed'
    for s in (-1,1):
        side='L' if s>0 else 'R'
        tube(f'{side}_Roof_Weld',[(x,y,z+.006) for x,y,z in upper if y*s>0],.0045,M['olive_dark'],c,TURRET)
        tube(f'{side}_Lower_Weld',[(x,y,z+.02) for x,y,z in lower if y*s>0],.005,M['olive_dark'],c,TURRET)
        # A narrow seam across the long turret side distinguishes the welded plates.
        tube(f'{side}_Turret_Side_Seam',[(.98,s*1.337,1.78),(.98,s*1.201,2.497)],.004,M['olive_dark'],c,TURRET)
        for x in (-.76,.56):
            handle(f'{side}_Turret_Grab_{x}',x,s*1.316,2.037,c,TURRET,.27)
        box(f'{side}_Side_Optical_Housing',(.68,s*1.281,2.107),(.37,.125,.235),M['olive_dark'],c,TURRET,.012)
        box(f'{side}_Side_Optical_Rim',(.68,s*1.354,2.107),(.31,.035,.185),M['olive_light'],c,TURRET,.006)
        box(f'{side}_Side_Optical_Glass',(.68,s*1.378,2.107),(.225,.011,.106),M['glass'],c,TURRET,.004)
        for x in (.548,.812):
            bolt(f'{side}_Optic_FrameBolt_{x}',(x,s*1.38,2.17),c,TURRET,(0,s,0),.008)
        for x,y,z in [(-.95,s*.91,2.49),(2.62,s*.84,2.48)]:
            torus(f'{side}_Turret_LiftingEye_{x}',(x,y,z+.042),.055,.019,M['olive_dark'],c,TURRET,(0,1,0))
    GUN=empty('Gun_Elevation_Pivot',c,(-1.26,0,2.009),TURRET)
    GUN['elevation_degrees']=0.0
    GUN.id_properties_ui('elevation_degrees').update(min=-9,max=20,description='Visual gun elevation in degrees; external model only')
    d=GUN.driver_add('rotation_euler',1).driver
    v=d.variables.new();v.name='elevation';v.targets[0].id=GUN;v.targets[0].data_path='["elevation_degrees"]'
    d.expression='elevation*pi/180'
    mantel_rings=[]
    for x,w,h in [(-1.76,.36,.24),(-1.61,.51,.35),(-1.25,.51,.36)]:
        mantel_rings.append([(x,-w,2.009-h),(x,w,2.009-h),(x,w,2.009+h),(x,-w,2.009+h)])
    loft('Gun_Mantlet_Armored_Shield',mantel_rings,M['olive'],c,GUN,.045)
    cyl('Gun_Mantlet_Collar',(-1.80,0,2.009),.192,.17,M['olive_dark'],c,GUN,(-1,0,0),64,.008)
    # Revolved hollow tube, with the conspicuous stepped fume extractor from the scan.
    profile=[(-5.218,.069),(-5.195,.077),(-5.116,.077),(-5.10,.068),
             (-3.625,.083),(-3.59,.085),(-3.55,.142),(-3.48,.151),
             (-3.14,.151),(-3.08,.132),(-3.02,.095),(-2.52,.106),
             (-2.50,.126),(-2.31,.126),(-2.28,.109),(-2.01,.118),
             (-1.95,.148),(-1.74,.148),(-1.74,.053),(-5.218,.053)]
    n=64
    verts=[(x,r*math.cos(i*math.tau/n),2.009+r*math.sin(i*math.tau/n)) for x,r in profile for i in range(n)]
    faces=[(j*n+i,j*n+(i+1)%n,((j+1)%len(profile))*n+(i+1)%n,((j+1)%len(profile))*n+i)
           for j in range(len(profile)) for i in range(n)]
    barrel=mesh('Gun_ExternalTube_HollowMuzzle',verts,faces,M['olive'],c,GUN,.0015)
    for p in barrel.data.polygons:
        p.use_smooth=True
    barrel['bore_diameter_m']=.105
    barrel['bore_assumption']='Visual estimate only. Scan does not settle 105 vs 120 mm prototype armament.'
    cyl('Gun_Bore_Interior',(-4.73,0,2.009),.0529,.012,M['black'],c,GUN,(1,0,0),48,0)
    for x,r in [(-5.15,.077),(-3.55,.145),(-3.16,.151),(-2.485,.128),(-2.325,.128),(-1.97,.149)]:
        torus(f'Gun_Collar_Seam_{x}',(x,0,2.009),r,.006,M['olive_dark'],c,GUN,(1,0,0))
    for angle in (0,math.pi/2,math.pi,3*math.pi/2):
        bolt(f'Mantlet_CollarBolt_{angle}',(-1.893,.171*math.cos(angle),2.009+.171*math.sin(angle)),c,GUN,(-1,0,0))
    return shell


def build_turret_fittings():
    c=collection('05 | Hatches optics smoke launchers and roof fittings',MODEL)
    for name,x,y,r in [('Commander',.45,-.60,.354),('Loader',.48,.64,.323)]:
        z=2.53
        cyl(name+'_Hatch_Seal',(x,y,z),r+.037,.035,M['rubber'],c,TURRET,vertices=64)
        cyl(name+'_Hatch_Ring',(x,y,z+.028),r+.043,.048,M['olive_dark'],c,TURRET,vertices=64)
        cyl(name+'_Hatch_Lid',(x,y,z+.063),r,.047,M['olive'],c,TURRET,vertices=64,bevel=.007)
        torus(name+'_Hatch_Lip',(x,y,z+.08),r-.015,.011,M['olive_light'],c,TURRET)
        handle(name+'_Hatch_Grab',x-.10,y,z+.093,c,TURRET)
        box(name+'_Hinge',(x+.30,y,z+.065),(.12,.20,.09),M['olive_dark'],c,TURRET)
        cyl(name+'_Hinge_Pin',(x+.31,y,z+.10),.026,.26,M['steel_dark'],c,TURRET,(0,1,0),24,0)
        cyl(name+'_Center_Boss',(x,y,z+.099),.064,.032,M['olive_dark'],c,TURRET)
        for a in range(6):
            theta=math.tau*a/6
            rod(f'{name}_Latch_Spoke_{a}',(x,y,z+.113),(x+.235*math.cos(theta),y+.235*math.sin(theta),z+.10),.017,M['olive_dark'],c,TURRET)
        if name=='Commander':
            for i in range(6):
                a=math.tau*i/6
                xx,yy=x+.413*math.cos(a),y+.413*math.sin(a)
                obj=box(f'Commander_Periscope_{i}',(xx,yy,z+.07),(.14,.092,.10),M['olive_dark'],c,TURRET)
                obj.rotation_euler.z=a-math.pi/2
                cyl(f'Commander_Periscope_Lens_{i}',(xx+.057*math.cos(a),yy+.057*math.sin(a),z+.08),.032,.009,M['glass'],c,TURRET,(math.cos(a),math.sin(a),0),24,0)
    # Main sight: an angular housing with a recessed frontal optical aperture.
    box('Primary_Sight_Plinth',(-.88,-.64,2.546),(.49,.42,.074),M['olive_dark'],c,TURRET,.009)
    box('Primary_Sight_Housing',(-.91,-.64,2.667),(.39,.33,.20),M['olive'],c,TURRET,.02)
    box('Primary_Sight_Shadow',(-1.114,-.64,2.672),(.013,.27,.12),M['black'],c,TURRET)
    box('Primary_Sight_Glass',(-1.123,-.64,2.676),(.009,.22,.079),M['glass'],c,TURRET)
    box('Primary_Sight_Shade',(-1.15,-.64,2.768),(.14,.375,.025),M['olive_dark'],c,TURRET)
    for s in (-1,1):
        side='L' if s>0 else 'R'
        for row in range(2):
            z=2.045+row*.232
            box(f'{side}_Smoke_Rack_{row}',(1.97+row*.20,s*1.263,z),(.94,.09,.11),M['olive_dark'],c,TURRET,.007)
            for i in range(4):
                start=Vector((1.61+i*.234+row*.20,s*1.28,z))
                axis=Vector((-.20,s*.74,.62)).normalized()
                cyl(f'{side}_SmokeTube_{row}_{i}',start+axis*.11,.050,.235,M['olive'],c,TURRET,axis,32,.003)
                cyl(f'{side}_SmokeCap_{row}_{i}',start+axis*.234,.054,.025,M['steel_dark'],c,TURRET,axis,32,.002)
                torus(f'{side}_SmokeRim_{row}_{i}',start+axis*.248,.044,.005,M['olive_light'],c,TURRET,axis)
                bolt(f'{side}_SmokeMount_{row}_{i}',tuple(start),c,TURRET,(0,s,0))
        for x in (1.14,2.55):
            handle(f'{side}_Roof_Grab_{x}',x,s*.98,2.523 if x<2 else 2.48,c,TURRET,.24)
        box(f'{side}_Turret_Rear_Stowage',(2.60,s*.94,2.498),(.40,.23,.15),M['olive_dark'],c,TURRET,.025)
        box(f'{side}_Rear_Stowage_Lid',(2.60,s*.94,2.578),(.414,.24,.023),M['olive'],c,TURRET)
    # Rear bustle vent, rails, and access cover.
    box('Turret_Rear_Vent_Recess',(3.006,0,2.14),(.032,.87,.36),M['black'],c,TURRET)
    for i in range(19):
        box(f'Turret_Rear_Vent_Slat_{i}',(3.028,-.40+i*.0444,2.14),(.044,.018,.33),M['olive_dark'],c,TURRET,.001)
    tube('Turret_Bustle_ProtectionRail',[(2.72,-1.12,2.33),(3.14,-1.04,2.33),
         (3.16,1.04,2.33),(2.72,1.12,2.33)],.018,M['olive_dark'],c,TURRET)
    for y in (-.83,.83):
        rod(f'Bustle_Rail_Standoff_{y}',(2.98,y,2.15),(3.145,y,2.33),.016,M['olive_dark'],c,TURRET)
    # Crosswind equipment mast and flexible radio whip, exterior interpretations.
    cyl('Crosswind_Sensor_Base',(2.09,.57,2.51),.080,.11,M['olive_dark'],c,TURRET)
    cyl('Crosswind_Sensor_Foot',(2.09,.57,2.60),.046,.10,M['olive'],c,TURRET)
    rod('Crosswind_Sensor_Mast',(2.09,.57,2.65),(2.09,.57,3.324),.015,M['steel_dark'],c,TURRET)
    torus('Crosswind_Sensor_Head',(2.09,.57,3.30),.048,.010,M['olive_dark'],c,TURRET,(1,0,0))
    rod('Crosswind_Sensor_HeadCross',(2.09,.52,3.30),(2.09,.62,3.30),.009,M['olive_dark'],c,TURRET)
    cyl('Radio_Antenna_Base',(2.52,-.72,2.57),.06,.13,M['rubber'],c,TURRET)
    for i in range(6):
        torus(f'Radio_Antenna_Spring_{i}',(2.52,-.72,2.60+i*.022),.027,.007,M['steel_dark'],c,TURRET)
    tube('Radio_Antenna_Whip',[(2.52,-.72,2.74),(2.55,-.72,3.02),(2.59,-.72,3.31)],.007,M['steel_dark'],c,TURRET)
    # Silhouette-level roof MG; external geometry only.
    cyl('Roof_MG_Pintle',(.29,-.69,2.733),.045,.25,M['steel_dark'],c,TURRET)
    box('Roof_MG_Receiver',(.08,-.69,2.848),(.46,.10,.115),M['steel_dark'],c,TURRET,.010)
    box('Roof_MG_FeedBox',(.05,-.79,2.843),(.21,.12,.17),M['olive_dark'],c,TURRET,.008)
    rod('Roof_MG_Barrel',(-.92,-.69,2.884),(-.12,-.69,2.884),.020,M['steel_dark'],c,TURRET)
    cyl('Roof_MG_Muzzle',(-.95,-.69,2.884),.027,.065,M['steel_dark'],c,TURRET,(-1,0,0),24,.001)
    for i in range(7):
        torus(f'Roof_MG_JacketRing_{i}',(-.65+i*.065,-.69,2.884),.026,.005,M['black'],c,TURRET,(1,0,0))
    box('Roof_MG_Stock',(.385,-.69,2.844),(.19,.07,.12),M['olive_dark'],c,TURRET,.013)
    rod('Roof_MG_FrontSight',(-.80,-.69,2.892),(-.80,-.69,2.93),.008,M['steel_dark'],c,TURRET)
    for y in (-.84,.84):
        for i in range(6):
            x=1.10+(2.67-1.10)*i/5
            z=2.513+max(x-1.39,0)/1.42*(2.445-2.513)+.007
            bolt(f'Turret_Roof_Bolt_{y}_{i}',(x,y,z),c,TURRET)


def add_references():
    c=collection('90 | Packed reference drawing (toggle visibility)',None)
    path=ROOT/'references'/'leopard2'/'reference_four_views.png'
    if not path.exists():
        path=Path('C:/Users/洪恒达/AppData/Local/Temp/codex-clipboard-35e8ca1c-1a6b-45aa-aaf7-a279cb46fd53.png')
    image=bpy.data.images.load(str(path),check_existing=True)
    image.pack()
    ref=bpy.data.objects.new('Reference_FourView_Original',None)
    c.objects.link(ref)
    ref.empty_display_type='IMAGE'
    ref.data=image
    ref.empty_display_size=14
    ref.location=(0,4,3.3)
    ref.rotation_euler=(math.pi/2,0,0)
    ref.color[3]=.5
    ref.hide_render=True
    ref['source']='User supplied four-view scan. Packed unchanged.'
    c.hide_viewport=True
    c.hide_render=True
    notes=bpy.data.texts.new('00_README_MODEL')
    notes.write('EARLY LEOPARD 2 PROTOTYPE | REFERENCE RECONSTRUCTION\n\n'
        'Units: meters. +Z up, gun forward -X. Exterior visualization model.\n'
        'Primary source: packed user four-view drawing. Exact prototype number unconfirmed.\n'
        'Select Turret_Pivot > Custom Properties > yaw_degrees to turn turret.\n'
        'Select Gun_Elevation_Pivot > Custom Properties > elevation_degrees to elevate gun.\n'
        'All attached fittings follow these pivots. Model_Root moves the entire vehicle.\n'
        'Individual shoes are linked editable meshes. Make single-user before changing only one.\n'
        'Bevel modifiers remain editable. Curves remain editable. No external textures required.\n'
        'Collections 90 and 99 hold reference and removable studio presentation.\n'
        'Drawing total length 9.613 m is prioritized; 5.218+4.400 gives 9.618 m,\n'
        'a 5 mm source discrepancy. Model rear extent uses +4.395 m.\n'
        'Gauge 2.785 m + track width .635 m = track outer width 3.420 m.\n'
        'Max fender width 3.700 m. Gun axis 2.009 m in neutral pose.\n'
        'The .105 m bore and unseen geometry are visual estimates, not verified mechanisms.\n'
        'No interior, manufacturing detail, vehicle physics or functional weapon system.\n'
        'See docs/leopard2/README_zh.md and references/leopard2/source-research.md.\n')


def camera(name, location, target, orthoscale, col):
    data=bpy.data.cameras.new(name)
    obj=bpy.data.objects.new(name,data);col.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=orthoscale;data.lens=48
    data.clip_end=200
    return obj


def studio(scene):
    c=collection('99 | Studio cameras and lighting (not model)')
    floor=material('Studio | neutral graphite',(.145,.16,.16),.12,.72)
    box('Studio_Floor',(0,0,-.067),(200,200,.12),floor,c,bevel=0)
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.31,.35,.38,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.48
    for name,loc,energy,size,color in [('Key',(-4,-5,10),2200,7,(1,.95,.86)),
                                    ('Fill',(-1,7,6),1800,6,(.80,.90,1)),
                                    ('Rim',(5,2,8),2600,5,(1,1,.98))]:
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
        obj=bpy.data.objects.new('Studio_'+name,data);c.objects.link(obj);obj.location=loc
        obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
    cams={
        'hero':camera('Camera_Hero',(-10.5,-12.5,8),(-.30,0,1.30),12.5,c),
        'rear':camera('Camera_Rear',(10,-11,7),(.25,0,1.38),11.4,c),
        'side':camera('Camera_Side',(0,-16,1.69),(-.4115,0,1.69),10.6,c),
        'top':camera('Camera_Top',(-.4115,0,18),(-.4115,0,0),10.6,c),
        'front':camera('Camera_Front',(-17,0,1.69),(0,0,1.69),4.65,c),
        'back':camera('Camera_Back',(17,0,1.69),(0,0,1.69),4.65,c),
    }
    scene.camera=cams['hero']
    scene.render.engine='CYCLES'
    scene.cycles.samples=48
    scene.cycles.use_denoising=True
    scene.cycles.max_bounces=5
    scene.cycles.transparent_max_bounces=4
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type='OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use=d.type=='OPTIX'
        if any(d.type=='OPTIX' for d in prefs.devices):
            scene.cycles.device='GPU'
    except Exception as exc:
        print('GPU setup fallback:',exc)
    scene.render.resolution_x=1600;scene.render.resolution_y=1100
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    return cams


def finish(scene, gear, cams, render=True, export_glb=True):
    bpy.context.view_layer.update()
    model_objects=list(MODEL.all_objects)
    # Center unique mesh origins without changing the world-space shape or pivot hierarchy.
    for obj in model_objects:
        if obj.type=='MESH' and obj.data.users==1:
            center=sum((Vector(v) for v in obj.bound_box),Vector())/8
            if center.length>1e-6:
                world=obj.matrix_world.copy()
                obj.data.transform(Matrix.Translation(-center))
                obj.matrix_world=world@Matrix.Translation(center)
    bpy.context.view_layer.update()
    for obj in model_objects:
        obj['model_asset']='Leopard 2 early prototype reference exterior'
    ROOT_OBJ['overall_length_m']=9.613
    ROOT_OBJ['overall_width_m']=3.700
    ROOT_OBJ['gun_axis_height_m']=2.009
    ROOT_OBJ['source_priority']='User scan dimensions first; reference family photos second'
    ROOT_OBJ['scope']='Editable exterior; interpolated details; exact prototype unknown'
    bpy.ops.object.select_all(action='DESELECT')
    TURRET.select_set(True);bpy.context.view_layer.objects.active=TURRET
    # A useful neutral editing view is saved in the project, with all parts visible.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.clip_end=1000
                area.spaces.active.shading.type='MATERIAL'
                area.spaces.active.region_3d.view_distance=13
                area.spaces.active.region_3d.view_location=Vector((-.3,0,1.2))
                area.spaces.active.region_3d.view_rotation=cams['hero'].rotation_euler.to_quaternion()
    blend=OUT/'Leopard_2_early_prototype_editable.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    manifest={'asset':blend.name,'blender':bpy.app.version_string,
              'interpretation':'Early Leopard 2 prototype family, exact PT/T unknown',
              'units':'meters','front_axis':'-X','up_axis':'+Z',
              'targets_m':{'overall_length':9.613,'overall_width':3.700,'gun_axis_height':2.009},
              'running_gear':gear,'objects':len(model_objects),
              'mesh_objects':sum(o.type=='MESH' for o in model_objects),
              'curve_objects':sum(o.type=='CURVE' for o in model_objects),
              'editable_modifiers':sum(len(o.modifiers) for o in model_objects),
              'source':'references/leopard2/reference_four_views.png',
              'assumptions_file':'references/leopard2/source-research.md',
              'controls':{'Turret_Pivot':'yaw_degrees','Gun_Elevation_Pivot':'elevation_degrees'}}
    (OUT/'model_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    if export_glb:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in model_objects:
            obj.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(OUT/'Leopard_2_early_prototype.glb'),
            export_format='GLB',use_selection=True,export_apply=True,
            export_animations=False,export_cameras=False,export_lights=False)
    if render:
        for name in ('hero','rear','side','top','front','back'):
            scene.camera=cams[name]
            bpy.data.objects['Studio_Floor'].hide_render=name in ('side','top','front','back')
            if name in ('side','top'):
                scene.render.resolution_x=1800;scene.render.resolution_y=760
            elif name in ('front','back'):
                scene.render.resolution_x=1000;scene.render.resolution_y=860
            else:
                scene.render.resolution_x=1600;scene.render.resolution_y=1100
            scene.render.filepath=str(PREVIEW/f'{name}.png')
            bpy.ops.render.render(write_still=True)
    print('MODEL_BUILD_COMPLETE',json.dumps(manifest))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-render',action='store_true')
    parser.add_argument('--no-glb',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    scene=reset()
    M=make_materials()
    MODEL=collection('LEOPARD 2 | Editable exterior')
    ROOT_OBJ=empty('Model_Root',MODEL)
    build_hull()
    build_hull_fittings()
    gear=build_running_gear(ROOT_OBJ,MODEL,M)
    build_turret()
    build_turret_fittings()
    add_references()
    cams=studio(scene)
    finish(scene,gear,cams,not args.no_render,not args.no_glb)
