"""Small Blender mesh helpers. Coordinates are world-space; parenting preserves them."""

import math

import bmesh
import bpy
from mathutils import Vector


def collection(name, parent=None):
    result = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(result)
    return result


def attach(obj, col, parent=None):
    col.objects.link(obj)
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def empty(name, col, location=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = 0.3
    attach(obj, col, parent)
    bpy.context.view_layer.update()
    return obj


def mesh(name, verts, faces, mat, col, parent=None, bevel=0):
    data = bpy.data.meshes.new(name + '_Mesh')
    data.from_pydata(verts, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    attach(obj, col, parent)
    if mat:
        data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('Editable edge bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        mod = obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        mod.keep_sharp = True
        mod.weight = 40
    return obj


def box(name, loc, dims, mat, col, parent=None, bevel=0.005):
    x, y, z = [d / 2 for d in dims]
    verts = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
             (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    obj = mesh(name, verts, faces, mat, col, None, bevel)
    obj.location = loc
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def cyl(name, loc, radius, depth, mat, col, parent=None, axis=(0,0,1), vertices=48, bevel=0.002):
    verts = [(radius*math.cos(2*math.pi*i/vertices),radius*math.sin(2*math.pi*i/vertices),z)
             for z in (-depth/2,depth/2) for i in range(vertices)]
    faces = [tuple(reversed(range(vertices))),tuple(range(vertices,vertices*2))]
    faces += [(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    obj = mesh(name, verts, faces, mat, col, None, bevel)
    obj.location = loc
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector(axis).to_track_quat('Z','Y')
    for p in obj.data.polygons[2:]:
        p.use_smooth = True
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def rod(name, a, b, radius, mat, col, parent=None):
    a, b = Vector(a), Vector(b)
    return cyl(name, (a+b)/2, radius, (b-a).length, mat, col, parent, b-a, 16, 0)


def tube(name, points, radius, mat, col, parent=None):
    data = bpy.data.curves.new(name+'_Curve', 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 1
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new('POLY')
    spline.points.add(len(points)-1)
    for p, co in zip(spline.points, points):
        p.co = (*co,1)
    obj = bpy.data.objects.new(name, data)
    data.materials.append(mat)
    return attach(obj, col, parent)


def torus(name, loc, major, minor, mat, col, parent=None, axis=(0,0,1)):
    n, m = 48, 10
    verts = []
    for i in range(n):
        t = i*math.tau/n
        for j in range(m):
            u = j*math.tau/m
            verts.append(((major+minor*math.cos(u))*math.cos(t),
                          (major+minor*math.cos(u))*math.sin(t),minor*math.sin(u)))
    faces = [(i*m+j,((i+1)%n)*m+j,((i+1)%n)*m+(j+1)%m,i*m+(j+1)%m)
             for i in range(n) for j in range(m)]
    obj = mesh(name, verts, faces, mat, col)
    obj.location = loc
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector(axis).to_track_quat('Z','Y')
    for p in obj.data.polygons:
        p.use_smooth = True
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def prism(name, polygon, z0, z1, mat, col, parent=None, bevel=0.006):
    n = len(polygon)
    verts = [(x,y,z) for z in (z0,z1) for x,y in polygon]
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name, verts, faces, mat, col, parent, bevel)


def loft(name, rings, mat, col, parent=None, bevel=0.005):
    n = len(rings[0])
    verts = [v for ring in rings for v in ring]
    faces = [tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]
    for r in range(len(rings)-1):
        faces += [(r*n+i,r*n+(i+1)%n,(r+1)*n+(i+1)%n,(r+1)*n+i) for i in range(n)]
    return mesh(name, verts, faces, mat, col, parent, bevel)


def material(name, color, metallic=0.0, roughness=0.5, noise=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color,1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if noise:
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 145
        tex.inputs['Detail'].default_value = 2
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.17
        bump.inputs['Distance'].default_value = 0.003
        links.new(tex.outputs['Fac'],bump.inputs['Height'])
        links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.18
        ramp.color_ramp.elements[0].color = (*(v*.75 for v in color),1)
        ramp.color_ramp.elements[1].position = .82
        ramp.color_ramp.elements[1].color = (*(v*1.15 for v in color),1)
        links.new(tex.outputs['Fac'],ramp.inputs[0])
        links.new(ramp.outputs[0],bsdf.inputs['Base Color'])
    return mat
