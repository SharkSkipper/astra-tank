"""Editable paired road wheels and individually instanced articulated tracks."""

import math

import bpy
from mathutils import Matrix, Vector

from tank_common import collection, cyl, empty, mesh, rod


def _lathe_y(name, location, profile, material, target, parent, segments=64):
    verts = []
    for radius, depth in profile:
        verts.extend(
            (location[0] + radius * math.cos(2 * math.pi * i / segments),
             location[1] + depth,
             location[2] + radius * math.sin(2 * math.pi * i / segments))
            for i in range(segments)
        )
    faces = []
    for ring in range(len(profile)):
        next_ring = (ring + 1) % len(profile)
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((ring * segments + i, next_ring * segments + i,
                          next_ring * segments + j, ring * segments + j))
    obj = mesh(name, verts, faces, material, target, parent=parent)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def _ring_y(name, location, inner, outer, depth, material, target, parent):
    return _lathe_y(name, location,
                    [(inner, -depth / 2), (outer, -depth / 2),
                     (outer, depth / 2), (inner, depth / 2)],
                    material, target, parent)


def _bolt_array(name, x, y, z, ring_radius, count, radius, target, material, parent):
    template = None
    template_position = None
    for index in range(count):
        angle = 2 * math.pi * index / count
        pos = (x + ring_radius * math.sin(angle), y,
               z + ring_radius * math.cos(angle))
        if template is None:
            bolt = cyl(f"{name}_{index + 1:02d}", pos, radius, .018, material,
                       target, parent=parent, axis=(0, 1, 0), vertices=6,
                       bevel=.0008)
            template = bolt
            template_position = Vector(pos)
        else:
            bolt = template.copy()
            bolt.data = template.data
            bolt.name = f"{name}_{index + 1:02d}"
            target.objects.link(bolt)
            bolt.location = template.location + Vector(pos) - template_position


def _wheel(name, x, y, z, side, target, materials, parent):
    assembly = empty(name, target, location=(x, y, z), parent=parent)
    _lathe_y(name + "_RubberTire", (x, y, z),
             [(.316, -.073), (.373, -.073), (.390, -.051),
              (.390, .051), (.373, .073), (.316, .073)],
             materials["rubber"], target, assembly)
    rim_profile = [(.072, -.061), (.290, -.061), (.317, -.070),
                   (.326, -.057), (.326, .057), (.317, .070),
                   (.296, .070), (.273, .049), (.161, .036),
                   (.119, .068), (.072, .068)]
    if side < 0:
        rim_profile = [(radius, -depth) for radius, depth in reversed(rim_profile)]
    _lathe_y(name + "_DishedRim", (x, y, z), rim_profile,
             materials["olive"], target, assembly)
    face_y = y + side * .074
    _ring_y(name + "_RimLip", (x, face_y, z), .292, .316, .012,
            materials["olive_dark"], target, assembly)
    _ring_y(name + "_BearingRing", (x, y + side * .078, z), .105, .128,
            .016, materials["steel_dark"], target, assembly)
    cyl(name + "_Hub", (x, y + side * .080, z), .105, .060,
        materials["olive"], target, parent=assembly, axis=(0, 1, 0), bevel=.006)
    cyl(name + "_HubCap", (x, y + side * .115, z), .073, .016,
        materials["olive_dark"], target, parent=assembly, axis=(0, 1, 0),
        vertices=48, bevel=.004)
    cyl(name + "_AxleCover", (x, y + side * .126, z), .035, .009,
        materials["steel_dark"], target, parent=assembly, axis=(0, 1, 0),
        vertices=8, bevel=.001)
    _bolt_array(name + "_HubBolt", x, y + side * .121, z, .086, 8, .010,
                target, materials["bolt"], assembly)
    _bolt_array(name + "_RimBolt", x, y + side * .073, z, .250, 12, .012,
                target, materials["olive_dark"], assembly)
    return assembly


def _convex_hull(points):
    points = sorted(set(points))

    def cross(o, a, b):
        return ((a[0] - o[0]) * (b[1] - o[1]) -
                (a[1] - o[1]) * (b[0] - o[0]))

    lower = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def _track_path():
    circles = [(-2.80, .88, .350), (-1.90, .46, .415),
               (2.98, .46, .415), (3.62, .94, .385)]
    samples = []
    for x, z, radius in circles:
        for i in range(360):
            angle = 2 * math.pi * i / 360
            samples.append((x + radius * math.cos(angle),
                            z + radius * math.sin(angle)))
    hull = _convex_hull(samples)
    lengths = []
    for index, point in enumerate(hull):
        nxt = hull[(index + 1) % len(hull)]
        lengths.append(math.hypot(nxt[0] - point[0], nxt[1] - point[1]))
    return hull, lengths, sum(lengths)


def _point_on_path(hull, lengths, distance):
    for index, length in enumerate(lengths):
        if distance <= length or index == len(lengths) - 1:
            point = hull[index]
            nxt = hull[(index + 1) % len(hull)]
            factor = distance / length
            return (point[0] + factor * (nxt[0] - point[0]),
                    point[1] + factor * (nxt[1] - point[1]))
        distance -= length


def _shoe_mesh(pitch, materials):
    verts, faces, indices = [], [], []

    def cuboid(center, dimensions, material_index):
        cx, cy, cz = center
        hx, hy, hz = (n / 2 for n in dimensions)
        offset = len(verts)
        verts.extend([(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
                      (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
                      (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
                      (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)])
        for face in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                     (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
            faces.append(tuple(offset + n for n in face))
            indices.append(material_index)

    def pin(x, y, depth, radius, material_index):
        offset = len(verts)
        segments = 12
        for end in [-depth / 2, depth / 2]:
            for index in range(segments):
                angle = 2 * math.pi * index / segments
                verts.append((x + radius * math.cos(angle), y + end,
                              radius * math.sin(angle)))
        faces.append(tuple(offset + n for n in range(segments)))
        indices.append(material_index)
        faces.append(tuple(offset + segments + n for n in reversed(range(segments))))
        indices.append(material_index)
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((offset + index, offset + segments + index,
                          offset + segments + nxt, offset + nxt))
            indices.append(material_index)

    shoe_length = pitch * .88
    cuboid((0, 0, 0), (shoe_length, .594, .040), 0)
    for y in [-.158, .158]:
        cuboid((0, y, -.0325), (shoe_length * .84, .252, .025), 1)
        cuboid((0, y, .025), (shoe_length * .76, .245, .012), 2)
    for y in [-.296, .296]:
        cuboid((0, y, .003), (shoe_length * 1.05, .037, .050), 2)
        pin(-pitch / 2, y, .043, .025, 2)
    pin(-pitch / 2, 0, .554, .019, 0)
    offset = len(verts)
    verts.extend([(-.051, -.030, .020), (.051, -.030, .020),
                  (.051, .030, .020), (-.051, .030, .020),
                  (-.025, -.011, .114), (.025, -.011, .114),
                  (.025, .011, .114), (-.025, .011, .114)])
    for face in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        faces.append(tuple(offset + n for n in face))
        indices.append(2)
    data = bpy.data.meshes.new("TrackShoe_SharedEditableMesh")
    data.from_pydata(verts, [], faces)
    data.materials.append(materials["steel_dark"])
    data.materials.append(materials["rubber"])
    data.materials.append(materials["steel"])
    for polygon, material_index in zip(data.polygons, indices):
        polygon.material_index = material_index
    data.update()
    return data


def _sprocket(name, x, y, z, side, target, materials, parent):
    assembly = empty(name, target, location=(x, y, z), parent=parent)
    for half in [-1, 1]:
        yy = y + half * .221
        _ring_y(name + f"_ToothRing_{half:+d}", (x, yy, z), .244, .308,
                .052, materials["steel_dark"], target, assembly)
        _ring_y(name + f"_WebRim_{half:+d}", (x, yy, z), .190, .254,
                .036, materials["olive"], target, assembly)
        cyl(name + f"_Hub_{half:+d}", (x, yy, z), .105, .09,
            materials["olive"], target, parent=assembly, axis=(0, 1, 0),
            vertices=48, bevel=.003)
        for spoke in range(10):
            angle = 2 * math.pi * spoke / 10
            a = (x + .10 * math.sin(angle), yy, z + .10 * math.cos(angle))
            b = (x + .228 * math.sin(angle), yy, z + .228 * math.cos(angle))
            rod(name + f"_WebSpoke_{half:+d}_{spoke + 1:02d}", a, b, .030,
                materials["olive"], target, parent=assembly)
        for tooth in range(20):
            angle = 2 * math.pi * tooth / 20
            radial = Vector((math.sin(angle), 0, math.cos(angle)))
            tangent = Vector((math.cos(angle), 0, -math.sin(angle)))
            center = Vector((x, yy, z))
            verts = []
            for depth in [-.028, .028]:
                for radius, width in [(.294, -.038), (.348, -.021),
                                      (.348, .021), (.294, .038)]:
                    point = center + radial * radius + tangent * width
                    point.y += depth
                    verts.append(tuple(point))
            faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
                     (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            mesh(name + f"_DriveTooth_{half:+d}_{tooth + 1:02d}", verts, faces,
                 materials["steel"], target, parent=assembly, bevel=.002)
        _bolt_array(name + f"_Fastener_{half:+d}", x, yy + side * .049,
                    z, .143, 10, .011, target, materials["bolt"], assembly)
    cyl(name + "_Axle", (x, y, z), .093, .54, materials["steel_dark"],
        target, parent=assembly, axis=(0, 1, 0), vertices=48)
    return assembly


def _idler(name, x, y, z, side, target, materials, parent):
    assembly = empty(name, target, location=(x, y, z), parent=parent)
    for half in [-1, 1]:
        yy = y + half * .157
        _ring_y(name + f"_RunningRim_{half:+d}", (x, yy, z), .238, .310,
                .095, materials["steel_dark"], target, assembly)
        _ring_y(name + f"_Flange_{half:+d}", (x, yy + side * .050, z),
                .230, .289, .018, materials["olive"], target, assembly)
        for spoke in range(8):
            angle = 2 * math.pi * spoke / 8
            a = (x + .08 * math.sin(angle), yy, z + .08 * math.cos(angle))
            b = (x + .251 * math.sin(angle), yy, z + .251 * math.cos(angle))
            rod(name + f"_Spoke_{half:+d}_{spoke + 1:02d}", a, b, .032,
                materials["olive"], target, parent=assembly)
        cyl(name + f"_Hub_{half:+d}", (x, yy, z), .103, .13,
            materials["olive"], target, parent=assembly, axis=(0, 1, 0),
            vertices=48, bevel=.004)
        cyl(name + f"_BearingCap_{half:+d}", (x, yy + side * .075, z),
            .070, .025, materials["olive_dark"], target, parent=assembly,
            axis=(0, 1, 0), vertices=32, bevel=.003)
        _bolt_array(name + f"_HubBolt_{half:+d}", x, yy + side * .089,
                    z, .084, 8, .010, target, materials["bolt"], assembly)
    return assembly


def build_running_gear(root, model_collection, M):
    running = collection("03 | Running gear and suspension", parent=model_collection)
    tracks = collection("06 | Individual linked track shoes", parent=model_collection)
    hull, lengths, perimeter = _track_path()
    link_count = 85
    pitch = perimeter / link_count
    shoe_data = _shoe_mesh(pitch, M)
    wheel_positions = [-1.90 + i * (4.88 / 6) for i in range(7)]
    for side, tag in [(1, "L"), (-1, "R")]:
        yy = side * 1.3925
        wheels_col = collection(f"{tag}_Road_Wheels_7_Paired_Stations", parent=running)
        ends_col = collection(f"{tag}_Idler_Drive_Return", parent=running)
        tracks_col = collection(f"{tag}_85_Articulated_Links", parent=tracks)
        side_root = empty(f"RunningGear_{tag}", running, parent=root)
        for index, x in enumerate(wheel_positions):
            station = empty(f"{tag}_RoadWheel_Station_{index + 1:02d}", wheels_col,
                            location=(x, yy, .46), parent=side_root)
            # The central gap admits the guide tooth of each passing track shoe.
            for half, label in [(-1, "Inner"), (1, "Outer")]:
                wheel_y = yy + side * half * .125
                _wheel(f"{tag}_RoadWheel_{index + 1:02d}_{label}", x, wheel_y,
                       .46, side, wheels_col, M, station)
            axle_y = side * 1.12
            cyl(f"{tag}_SuspensionAxle_{index + 1:02d}", (x, axle_y, .46),
                .094, .40, M["steel_dark"], wheels_col, parent=station,
                axis=(0, 1, 0), vertices=32)
            rod(f"{tag}_TrailingArm_{index + 1:02d}",
                (x - .29, side * 1.06, .75), (x, side * 1.12, .46), .072,
                M["olive_dark"], wheels_col, parent=station)
        _idler(f"{tag}_FrontIdler", -2.80, yy, .88, side, ends_col, M, side_root)
        _sprocket(f"{tag}_RearDriveSprocket", 3.62, yy, .94, side,
                  ends_col, M, side_root)
        for index, x in enumerate([-1.52, -.20, 1.18, 2.51]):
            roller_z = 1.098 + (x + 2.80) / 6.42 * .095
            roller = empty(f"{tag}_ReturnRoller_{index + 1:02d}", ends_col,
                           location=(x, yy, roller_z), parent=side_root)
            cyl(f"{tag}_ReturnRollerRubber_{index + 1:02d}", (x, yy, roller_z),
                .112, .35, M["rubber"], ends_col, parent=roller,
                axis=(0, 1, 0), vertices=32, bevel=.005)
            cyl(f"{tag}_ReturnRollerHub_{index + 1:02d}",
                (x, yy + side * .181, roller_z), .071, .020, M["olive"],
                ends_col, parent=roller, axis=(0, 1, 0), vertices=32)
        for index in range(link_count):
            distance = pitch * index
            x, z = _point_on_path(hull, lengths, distance)
            a = _point_on_path(hull, lengths, (distance - .02) % perimeter)
            b = _point_on_path(hull, lengths, (distance + .02) % perimeter)
            tangent = Vector((b[0] - a[0], 0, b[1] - a[1])).normalized()
            transverse = Vector((0, 1, 0))
            inward = tangent.cross(transverse)
            orientation = Matrix((tangent, transverse, inward)).transposed().to_4x4()
            orientation.translation = (x, yy, z)
            # Settle the finite shoe corners against the ground near the end-wheel tangent.
            lowest = min((orientation @ v.co).z for v in shoe_data.vertices)
            if lowest < 0:
                orientation.translation.z -= lowest
            obj = bpy.data.objects.new(f"{tag}_TrackLink_{index + 1:03d}", shoe_data)
            tracks_col.objects.link(obj)
            obj.parent = side_root
            obj.matrix_world = orientation
            obj["link_index"] = index + 1
            obj["track_side"] = tag
            obj["pitch_m"] = round(pitch, 5)
        side_root["road_wheel_stations"] = 7
        side_root["track_link_count"] = link_count
    return {"road_wheel_stations_per_side": 7,
            "paired_road_wheels_per_side": 14,
            "track_links_per_side": link_count,
            "track_shoe_width_m": .635,
            "track_outer_width_m": 3.420,
            "track_pitch_m": round(pitch, 5)}
