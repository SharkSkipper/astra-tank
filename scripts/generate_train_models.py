"""Build a traceable multi-part baseline scene for QJ 2655 and CR400AF.

This script is deliberately conservative: it creates separate objects for every
major component and writes reference IDs into Blender custom properties. It is
not an Astra run and must not be presented as one.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"
ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


COLORS = {
    "black": (0.045, 0.055, 0.07, 1.0),
    "boiler": (0.10, 0.115, 0.13, 1.0),
    "metal": (0.22, 0.25, 0.28, 1.0),
    "steel": (0.42, 0.48, 0.52, 1.0),
    "red": (0.55, 0.025, 0.02, 1.0),
    "cream": (0.86, 0.82, 0.71, 1.0),
    "blue_glass": (0.015, 0.08, 0.13, 1.0),
    "track": (0.12, 0.14, 0.15, 1.0),
    "wood": (0.22, 0.12, 0.06, 1.0),
    "warning": (0.9, 0.45, 0.05, 1.0),
}


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.name != "Collection":
            bpy.data.collections.remove(collection)


def collection(name: str, parent=None):
    item = bpy.data.collections.get(name)
    if item is None:
        item = bpy.data.collections.new(name)
    if parent is None:
        parent = bpy.context.scene.collection
    if item.name not in parent.children.keys():
        parent.children.link(item)
    return item


def move_to_collection(obj, target) -> None:
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    target.objects.link(obj)


def material(name: str, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


MATERIALS = {
    "black": material("QJ_Black", COLORS["black"], 0.55, 0.28),
    "boiler": material("QJ_Boiler", COLORS["boiler"], 0.7, 0.24),
    "metal": material("Rail_Metal", COLORS["metal"], 0.85, 0.22),
    "steel": material("Polished_Steel", COLORS["steel"], 0.9, 0.16),
    "red": material("CR400AF_Red", COLORS["red"], 0.15, 0.3),
    "cream": material("CR400AF_Cream", COLORS["cream"], 0.1, 0.34),
    "blue_glass": material("Window_Blue", COLORS["blue_glass"], 0.15, 0.12),
    "track": material("Track", COLORS["track"], 0.65, 0.32),
    "wood": material("Sleeper_Wood", COLORS["wood"], 0.0, 0.72),
    "warning": material("Reference_Accent", COLORS["warning"], 0.2, 0.3),
}


def mark(obj, subject: str, role: str, refs: str) -> None:
    obj["subject"] = subject
    obj["component_role"] = role
    obj["reference_ids"] = refs
    obj["generated_by"] = "procedural baseline; not an Astra run"


def add_empty(name: str, target_collection, location=(0, 0, 0), parent=None, subject=None, role="assembly", refs=""):
    obj = bpy.data.objects.new(name, None)
    target_collection.objects.link(obj)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.35
    obj.location = location
    obj.parent = parent
    if subject:
        mark(obj, subject, role, refs)
    return obj


def add_cube(
    name: str,
    location,
    dimensions,
    target_collection,
    mat,
    parent,
    subject: str,
    role: str,
    refs: str,
    bevel=0.0,
    rotation=(0, 0, 0),
):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new(name="soft_edges", type="BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    move_to_collection(obj, target_collection)
    obj.parent = parent
    obj.data.materials.append(mat)
    mark(obj, subject, role, refs)
    return obj


def add_cylinder(
    name: str,
    location,
    radius: float,
    depth: float,
    rotation,
    target_collection,
    mat,
    parent,
    subject: str,
    role: str,
    refs: str,
    vertices=32,
):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    move_to_collection(obj, target_collection)
    obj.parent = parent
    obj.data.materials.append(mat)
    mark(obj, subject, role, refs)
    return obj


def add_component(assembly, target_collection, name: str, subject: str, role: str, refs: str):
    return add_empty(name, target_collection, parent=assembly, subject=subject, role=role, refs=refs)


def create_tracks(root_collection):
    track_collection = collection("Shared_Two_Parallel_Tracks", root_collection)
    track_mat = MATERIALS["track"]
    sleeper_mat = MATERIALS["wood"]
    for track_index, y in enumerate((-4.5, 4.5), start=1):
        add_cube(
            f"Track_{track_index}_Rail_Left",
            (0, y - 0.72, 0.15),
            (34, 0.12, 0.18),
            track_collection,
            track_mat,
            None,
            "shared scene",
            "rail",
            "scene-track",
        )
        add_cube(
            f"Track_{track_index}_Rail_Right",
            (0, y + 0.72, 0.15),
            (34, 0.12, 0.18),
            track_collection,
            track_mat,
            None,
            "shared scene",
            "rail",
            "scene-track",
        )
        for sleeper_index, x in enumerate(range(-16, 17, 2), start=1):
            add_cube(
                f"Track_{track_index}_Sleeper_{sleeper_index:02d}",
                (x, y, 0.02),
                (0.42, 2.2, 0.16),
                track_collection,
                sleeper_mat,
                None,
                "shared scene",
                "sleeper",
                "scene-track",
            )


def create_qj(y: float, root_collection):
    subject = "QJ 2655"
    assembly_collection = collection("QJ_steam_locomotive", root_collection)
    body_collection = collection("QJ_body", assembly_collection)
    gear_collection = collection("QJ_running_gear", assembly_collection)
    brake_collection = collection("QJ_brake_structure", assembly_collection)
    tender_collection = collection("QJ_tender", assembly_collection)
    fittings_collection = collection("QJ_front_fittings", assembly_collection)
    coupling_collection = collection("QJ_coupling", assembly_collection)
    assembly = add_empty("QJ_Assembly", assembly_collection, location=(0, y, 0), subject=subject, refs="QJ-side,QJ-three-quarter")

    frame = add_component(assembly, body_collection, "QJ_Frame_Group", subject, "frame", "QJ-side")
    add_cube("QJ_Frame", (-0.5, y, 1.05), (20.0, 2.8, 0.55), body_collection, MATERIALS["black"], frame, subject, "frame", "QJ-side")
    add_cube("QJ_Deck", (-0.4, y, 1.65), (18.5, 3.0, 0.28), body_collection, MATERIALS["metal"], frame, subject, "deck", "QJ-side")

    boiler = add_component(assembly, body_collection, "QJ_Boiler_Group", subject, "boiler", "QJ-side,QJ-three-quarter")
    add_cylinder("QJ_Boiler", (-0.8, y, 3.15), 1.35, 11.0, (0, math.pi / 2, 0), body_collection, MATERIALS["boiler"], boiler, subject, "boiler", "QJ-side")
    add_cylinder("QJ_Smoke_Box", (-6.35, y, 3.15), 1.42, 1.0, (0, math.pi / 2, 0), body_collection, MATERIALS["black"], boiler, subject, "smoke box", "QJ-front-detail")
    add_cylinder("QJ_Smoke_Box_Door", (-6.88, y, 3.15), 1.2, 0.16, (0, math.pi / 2, 0), body_collection, MATERIALS["metal"], boiler, subject, "smoke box door", "QJ-front-detail")

    cab = add_component(assembly, body_collection, "QJ_Cab_Group", subject, "cab", "QJ-side,QJ-three-quarter")
    add_cube("QJ_Cab", (4.9, y, 3.15), (3.8, 2.95, 3.75), body_collection, MATERIALS["black"], cab, subject, "cab", "QJ-side")
    add_cube("QJ_Cab_Roof", (4.9, y, 5.1), (4.4, 3.25, 0.3), body_collection, MATERIALS["metal"], cab, subject, "cab roof", "QJ-side")
    for side in (-1, 1):
        add_cube(f"QJ_Cab_Window_{'L' if side < 0 else 'R'}", (4.8, y + side * 1.51, 3.8), (1.35, 0.08, 0.82), body_collection, MATERIALS["blue_glass"], cab, subject, "cab window", "QJ-three-quarter")

    running = add_component(assembly, gear_collection, "QJ_Running_Gear_Group", subject, "running gear", "QJ-side,QJ-front-detail")
    wheel_x = (-5.0, -2.5, 0.0, 2.5, 5.0)
    for index, x in enumerate(wheel_x, start=1):
        for side, side_name in ((-1, "L"), (1, "R")):
            add_cylinder(
                f"QJ_Driving_Wheel_{side_name}_{index:02d}",
                (x, y + side * 1.48, 1.55),
                1.02,
                0.32,
                (math.pi / 2, 0, 0),
                gear_collection,
                MATERIALS["steel"],
                running,
                subject,
                "driving wheel",
                "QJ-side,QJ-front-detail",
            )
            add_cylinder(
                f"QJ_Wheel_Hub_{side_name}_{index:02d}",
                (x, y + side * 1.68, 1.55),
                0.25,
                0.12,
                (math.pi / 2, 0, 0),
                gear_collection,
                MATERIALS["black"],
                running,
                subject,
                "wheel hub",
                "QJ-side",
            )
        add_cylinder(
            f"QJ_Driving_Axle_{index:02d}",
            (x, y, 1.55),
            0.12,
            3.25,
            (math.pi / 2, 0, 0),
            gear_collection,
            MATERIALS["steel"],
            running,
            subject,
            "driving axle",
            "QJ-side,QJ-front-detail",
        )
    for x, wheel_label in ((-7.0, "Leading"), (5.8, "Trailing")):
        for side, side_name in ((-1, "L"), (1, "R")):
            add_cylinder(
                f"QJ_{wheel_label}_Wheel_{side_name}",
                (x, y + side * 1.42, 1.35),
                0.65,
                0.28,
                (math.pi / 2, 0, 0),
                gear_collection,
                MATERIALS["steel"],
                running,
                subject,
                "leading/trailing wheel",
                "QJ-side,QJ-front-detail",
            )
    for side, side_name in ((-1, "L"), (1, "R")):
        add_cube(f"QJ_Side_Rod_{side_name}", (-0.1, y + side * 1.77, 1.55), (10.7, 0.14, 0.2), gear_collection, MATERIALS["metal"], running, subject, "side rod", "QJ-side")
        add_cube(f"QJ_Main_Rod_{side_name}", (-1.2, y + side * 1.9, 1.55), (5.9, 0.18, 0.28), gear_collection, MATERIALS["steel"], running, subject, "main rod", "QJ-side,QJ-front-detail")
        for index, x in enumerate(wheel_x, start=1):
            add_cylinder(f"QJ_Rod_Pin_{side_name}_{index:02d}", (x, y + side * 1.87, 1.55), 0.16, 0.08, (math.pi / 2, 0, 0), gear_collection, MATERIALS["warning"], running, subject, "rod pin", "QJ-side")
    add_cube("QJ_Pilot_Frame", (-7.8, y, 1.15), (2.0, 2.4, 0.24), gear_collection, MATERIALS["metal"], running, subject, "pilot frame", "QJ-front-detail")

    brakes = add_component(assembly, brake_collection, "QJ_Brake_Structure_Group", subject, "brake structure", "QJ-side,QJ-front-detail")
    for side, side_name in ((-1, "L"), (1, "R")):
        add_cube(f"QJ_Brake_Rigging_{side_name}", (0.0, y + side * 1.34, 1.05), (8.5, 0.10, 0.16), brake_collection, MATERIALS["metal"], brakes, subject, "brake rigging", "QJ-side")
        add_cube(f"QJ_Brake_Cylinder_{side_name}", (2.8, y + side * 1.32, 1.15), (1.15, 0.18, 0.22), brake_collection, MATERIALS["steel"], brakes, subject, "brake cylinder", "QJ-front-detail")
        for index, x in enumerate((-5.0, -2.5, 0.0, 2.5, 5.0), start=1):
            add_cube(f"QJ_Brake_Shoe_{side_name}_{index:02d}", (x, y + side * 1.23, 1.35), (0.22, 0.10, 0.48), brake_collection, MATERIALS["warning"], brakes, subject, "brake shoe", "QJ-front-detail")

    fittings = add_component(assembly, fittings_collection, "QJ_Front_Fittings_Group", subject, "front fittings", "QJ-front-detail")
    add_cylinder("QJ_Chimney", (-7.0, y, 4.8), 0.46, 1.7, (0, 0, 0), fittings_collection, MATERIALS["metal"], fittings, subject, "chimney", "QJ-front-detail")
    add_cylinder("QJ_Chimney_Cap", (-7.0, y, 5.7), 0.7, 0.18, (0, 0, 0), fittings_collection, MATERIALS["black"], fittings, subject, "chimney cap", "QJ-front-detail")
    for index, x in enumerate((-3.4, -1.7, 0.0), start=1):
        add_cylinder(f"QJ_Dome_{index}", (x, y, 4.5), 0.42, 0.45, (0, 0, 0), fittings_collection, MATERIALS["metal"], fittings, subject, "steam dome", "QJ-side")
    add_cylinder("QJ_Headlamp", (-7.5, y, 4.55), 0.35, 0.35, (0, math.pi / 2, 0), fittings_collection, MATERIALS["warning"], fittings, subject, "headlamp", "QJ-front-detail")
    for side, side_name in ((-1, "L"), (1, "R")):
        add_cube(f"QJ_Cab_Handrail_{side_name}", (1.3, y + side * 1.56, 3.4), (7.0, 0.08, 0.08), fittings_collection, MATERIALS["steel"], fittings, subject, "handrail", "QJ-side")
        add_cube(f"QJ_Boiler_Pipe_{side_name}", (-2.0, y + side * 1.42, 2.35), (7.0, 0.09, 0.09), fittings_collection, MATERIALS["steel"], fittings, subject, "boiler pipe", "QJ-side")

    tender = add_component(assembly, tender_collection, "QJ_Tender_Group", subject, "tender", "QJ-side,QJ-three-quarter")
    add_cube("QJ_Tender_Body", (9.0, y, 2.5), (5.8, 3.0, 2.7), tender_collection, MATERIALS["black"], tender, subject, "tender", "QJ-side")
    add_cube("QJ_Tender_Top", (9.0, y, 3.95), (5.9, 3.05, 0.3), tender_collection, MATERIALS["metal"], tender, subject, "tender top", "QJ-side")
    for index, x in enumerate((7.3, 9.9), start=1):
        for side, side_name in ((-1, "L"), (1, "R")):
            add_cylinder(f"QJ_Tender_Wheel_{side_name}_{index:02d}", (x, y + side * 1.48, 1.3), 0.78, 0.3, (math.pi / 2, 0, 0), gear_collection, MATERIALS["steel"], tender, subject, "tender wheel", "QJ-side")

    coupling = add_component(assembly, coupling_collection, "QJ_Coupling_Group", subject, "coupling", "QJ-front-detail,QJ-side")
    for x, side_label in ((-8.7, "Front"), (12.2, "Rear")):
        add_cube(f"QJ_Buffer_Beam_{side_label}", (x, y, 1.2), (0.35, 2.4, 0.3), coupling_collection, MATERIALS["metal"], coupling, subject, "buffer beam", "QJ-front-detail")
        for side, side_name in ((-1, "L"), (1, "R")):
            add_cylinder(f"QJ_Buffer_{side_label}_{side_name}", (x, y + side * 0.88, 1.35), 0.22, 0.45, (0, math.pi / 2, 0), coupling_collection, MATERIALS["steel"], coupling, subject, "buffer", "QJ-front-detail")

    return assembly


def create_cr400af(y: float, root_collection):
    subject = "CR400AF"
    assembly_collection = collection("CR400AF_emu", root_collection)
    body_collection = collection("CR400AF_body", assembly_collection)
    gear_collection = collection("CR400AF_running_gear", assembly_collection)
    interior_collection = collection("CR400AF_interior", assembly_collection)
    underframe_collection = collection("CR400AF_underframe", assembly_collection)
    roof_collection = collection("CR400AF_roof_equipment", assembly_collection)
    detail_collection = collection("CR400AF_doors_windows", assembly_collection)
    coupling_collection = collection("CR400AF_coupling", assembly_collection)
    assembly = add_empty("CR400AF_Assembly", assembly_collection, location=(0, y, 0), subject=subject, refs="CR400AF-front,CR400AF-side,CR400AF-bogie")

    body = add_component(assembly, body_collection, "CR400AF_Car_Bodies_Group", subject, "car bodies", "CR400AF-front,CR400AF-side")
    cars = (-8.2, 0.0, 8.2)
    for car_index, x in enumerate(cars, start=1):
        add_cube(f"CR400AF_Car_Body_{car_index:02d}", (x, y, 3.2), (7.8, 3.05, 3.15), body_collection, MATERIALS["cream"], body, subject, "car body", "CR400AF-side")
        add_cube(f"CR400AF_Car_Lower_Skirt_{car_index:02d}", (x, y, 2.0), (7.9, 3.18, 0.55), body_collection, MATERIALS["red"], body, subject, "lower skirt", "CR400AF-side")
        for side, side_name in ((-1, "L"), (1, "R")):
            add_cube(f"CR400AF_Red_Stripe_{car_index:02d}_{side_name}", (x, y + side * 1.55, 3.0), (7.7, 0.06, 0.18), body_collection, MATERIALS["red"], body, subject, "livery stripe", "CR400AF-side")

    nose = add_component(assembly, body_collection, "CR400AF_Nose_Group", subject, "nose", "CR400AF-front,CR400AF-line-scan")
    add_cube("CR400AF_Nose_Front", (-12.3, y, 3.25), (1.9, 2.95, 2.95), body_collection, MATERIALS["cream"], nose, subject, "aerodynamic nose", "CR400AF-front")
    add_cube("CR400AF_Nose_Rear", (12.3, y, 3.25), (1.9, 2.95, 2.95), body_collection, MATERIALS["cream"], nose, subject, "aerodynamic nose", "CR400AF-front")
    add_cube("CR400AF_Nose_Red_Band_Front", (-12.3, y - 1.51, 3.0), (1.9, 0.06, 0.2), body_collection, MATERIALS["red"], nose, subject, "nose livery", "CR400AF-front")
    add_cube("CR400AF_Nose_Red_Band_Rear", (12.3, y - 1.51, 3.0), (1.9, 0.06, 0.2), body_collection, MATERIALS["red"], nose, subject, "nose livery", "CR400AF-front")
    for x, side_label in ((-13.25, "Front"), (13.25, "Rear")):
        add_cube(f"CR400AF_Cab_Glass_{side_label}", (x, y, 3.85), (0.08, 2.2, 0.82), detail_collection, MATERIALS["blue_glass"], nose, subject, "cab glass", "CR400AF-front,CR400AF-line-scan")
        add_cube(f"CR400AF_Headlight_{side_label}", (x, y - 1.15, 3.0), (0.08, 0.22, 0.18), detail_collection, MATERIALS["warning"], nose, subject, "headlight", "CR400AF-front")

    details = add_component(assembly, detail_collection, "CR400AF_Doors_Windows_Group", subject, "doors and windows", "CR400AF-side,CR400AF-front")
    for car_index, x in enumerate(cars, start=1):
        window_positions = (x - 2.4, x - 1.2, x, x + 1.2, x + 2.4)
        for side, side_name in ((-1, "L"), (1, "R")):
            for window_index, window_x in enumerate(window_positions, start=1):
                add_cube(f"CR400AF_Window_{car_index:02d}_{side_name}_{window_index:02d}", (window_x, y + side * 1.56, 3.65), (0.82, 0.06, 0.63), detail_collection, MATERIALS["blue_glass"], details, subject, "window", "CR400AF-side")
            for door_index, door_x in enumerate((x - 3.0, x + 3.0), start=1):
                add_cube(f"CR400AF_Door_{car_index:02d}_{side_name}_{door_index:02d}", (door_x, y + side * 1.58, 3.0), (0.92, 0.07, 1.9), detail_collection, MATERIALS["metal"], details, subject, "door", "CR400AF-side")

    running = add_component(assembly, gear_collection, "CR400AF_Bogies_Group", subject, "bogies and wheelsets", "CR400AF-bogie,CR400AF-side")
    for car_index, x in enumerate(cars, start=1):
        for bogie_index, bogie_x in enumerate((x - 2.2, x + 2.2), start=1):
            bogie = add_component(running, gear_collection, f"CR400AF_Bogie_{car_index:02d}_{bogie_index:02d}", subject, "bogie", "CR400AF-bogie")
            add_cube(f"CR400AF_Bogie_Frame_{car_index:02d}_{bogie_index:02d}", (bogie_x, y, 1.1), (2.15, 2.35, 0.38), gear_collection, MATERIALS["metal"], bogie, subject, "bogie frame", "CR400AF-bogie")
            for wheel_index, wheel_x in enumerate((bogie_x - 0.7, bogie_x + 0.7), start=1):
                for side, side_name in ((-1, "L"), (1, "R")):
                    add_cylinder(f"CR400AF_Wheel_{car_index:02d}_{bogie_index:02d}_{side_name}_{wheel_index:02d}", (wheel_x, y + side * 1.25, 0.8), 0.48, 0.22, (math.pi / 2, 0, 0), gear_collection, MATERIALS["steel"], bogie, subject, "wheelset", "CR400AF-bogie")
            add_cube(f"CR400AF_Axle_{car_index:02d}_{bogie_index:02d}", (bogie_x, y, 0.8), (2.2, 0.22, 0.22), gear_collection, MATERIALS["steel"], bogie, subject, "axle", "CR400AF-bogie")

    interior = add_component(assembly, interior_collection, "CR400AF_Interior_Regions_Group", subject, "interior regions", "CR400AF-side")
    for car_index, x in enumerate(cars, start=1):
        add_cube(f"CR400AF_Interior_Floor_{car_index:02d}", (x, y, 2.55), (7.2, 2.35, 0.12), interior_collection, MATERIALS["metal"], interior, subject, "interior floor", "CR400AF-side")
        for seat_index, seat_x in enumerate((x - 1.5, x + 1.5), start=1):
            add_cube(f"CR400AF_Interior_Seat_{car_index:02d}_{seat_index:02d}", (seat_x, y, 2.95), (0.62, 1.35, 0.45), interior_collection, MATERIALS["blue_glass"], interior, subject, "interior simplified seat zone", "CR400AF-side")

    underframe = add_component(assembly, underframe_collection, "CR400AF_Underframe_Equipment_Group", subject, "underframe equipment", "CR400AF-bogie,CR400AF-side")
    for car_index, x in enumerate(cars, start=1):
        add_cube(f"CR400AF_Underframe_Equipment_{car_index:02d}", (x, y, 1.55), (2.8, 1.55, 0.34), underframe_collection, MATERIALS["black"], underframe, subject, "underframe equipment", "CR400AF-bogie,CR400AF-side")

    roof = add_component(assembly, roof_collection, "CR400AF_Roof_Equipment_Group", subject, "roof equipment", "CR400AF-side,CR400AF-front")
    for car_index, x in enumerate(cars, start=1):
        add_cube(f"CR400AF_Roof_{car_index:02d}", (x, y, 4.9), (7.8, 2.7, 0.22), roof_collection, MATERIALS["cream"], roof, subject, "roof", "CR400AF-side")
    for panto_index, x in enumerate((-1.2, 1.2), start=1):
        add_cube(f"CR400AF_Pantograph_Base_{panto_index:02d}", (x, y, 5.18), (0.95, 0.55, 0.12), roof_collection, MATERIALS["metal"], roof, subject, "pantograph base", "CR400AF-side")
        add_cube(f"CR400AF_Pantograph_Left_{panto_index:02d}", (x - 0.42, y, 5.65), (0.1, 0.1, 1.05), roof_collection, MATERIALS["steel"], roof, subject, "pantograph arm", "CR400AF-side", rotation=(0, -0.48, 0))
        add_cube(f"CR400AF_Pantograph_Right_{panto_index:02d}", (x + 0.42, y, 5.65), (0.1, 0.1, 1.05), roof_collection, MATERIALS["steel"], roof, subject, "pantograph arm", "CR400AF-side", rotation=(0, 0.48, 0))
        add_cube(f"CR400AF_Pantograph_Contact_{panto_index:02d}", (x, y, 6.1), (1.05, 0.12, 0.1), roof_collection, MATERIALS["steel"], roof, subject, "pantograph contact strip", "CR400AF-side")
    add_cube("CR400AF_Roof_Main_Bus", (0, y, 5.22), (14.0, 0.18, 0.18), roof_collection, MATERIALS["metal"], roof, subject, "roof bus", "CR400AF-side")

    coupling = add_component(assembly, coupling_collection, "CR400AF_Coupling_Group", subject, "coupling", "CR400AF-front,CR400AF-side")
    for index, x in enumerate((-4.05, 4.05), start=1):
        add_cube(f"CR400AF_Coupler_{index:02d}", (x, y, 1.5), (0.3, 0.65, 0.35), coupling_collection, MATERIALS["steel"], coupling, subject, "coupler", "CR400AF-front")
        add_cube(f"CR400AF_Connection_Bellows_{index:02d}", (x, y, 2.7), (0.22, 2.4, 1.15), coupling_collection, MATERIALS["black"], coupling, subject, "inter-car connection", "CR400AF-side")

    return assembly


def point_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def create_camera_and_lights(scene):
    bpy.ops.object.camera_add(location=(27.5, -31.0, 18.0))
    camera = bpy.context.object
    camera.name = "Camera_Two_Track_Comparison"
    camera.data.lens = 52
    point_camera(camera, (0, 0, 2.6))
    scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(2, -8, 18))
    key = bpy.context.object
    key.name = "Light_Key"
    key.data.energy = 1900
    key.data.shape = "RECTANGLE"
    key.data.size = 14
    point_camera(key, (0, 0, 2.0))

    bpy.ops.object.light_add(type="AREA", location=(-12, 14, 10))
    fill = bpy.context.object
    fill.name = "Light_Fill"
    fill.data.energy = 1100
    fill.data.size = 12
    point_camera(fill, (0, 0, 2.5))

    bpy.ops.object.light_add(type="AREA", location=(12, 0, 7))
    rim = bpy.context.object
    rim.name = "Light_Rim"
    rim.data.energy = 1400
    rim.data.size = 8
    point_camera(rim, (0, 0, 3.5))


def configure_render(scene):
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(ASSETS_DIR / "two_track_baseline_preview.png")
    scene.render.fps = 30
    scene.world.color = (0.012, 0.016, 0.022)


def export_selected(prefix: str, output_path: Path):
    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(prefix):
            obj.select_set(True)
            selected.append(obj)
    bpy.context.view_layer.objects.active = selected[0] if selected else None
    if not selected:
        raise RuntimeError(f"No objects selected for {prefix}")
    try:
        bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLB", use_selection=True, export_apply=True)
    except TypeError:
        bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLB", use_selection=True)
    bpy.ops.object.select_all(action="DESELECT")


def object_manifest(prefix: str):
    objects = []
    roles = set()
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(prefix):
            role = obj.get("component_role", "unknown")
            roles.add(role)
            objects.append({
                "name": obj.name,
                "type": obj.type,
                "role": role,
                "reference_ids": obj.get("reference_ids", ""),
            })
    return {"object_count": len(objects), "roles": sorted(roles), "objects": objects}


def save_individual(prefix: str, other_collection_name: str, blend_path: Path, glb_path: Path):
    other = bpy.data.collections.get(other_collection_name)
    if other:
        other.hide_viewport = True
        other.hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    export_selected(prefix, glb_path)
    if other:
        other.hide_viewport = False
        other.hide_render = False


def main():
    clear_scene()
    root = collection("TRAIN_PROJECT_ROOT")
    create_tracks(root)
    create_qj(-4.5, root)
    create_cr400af(4.5, root)

    scene = bpy.context.scene
    create_camera_and_lights(scene)
    configure_render(scene)

    scene["project"] = "dual-track-real-train-modeling"
    scene["reference_policy"] = "real photos and drawings first; every major part carries reference_ids"
    scene["model_policy"] = "separate editable components; no single joined shell"
    scene["baseline_status"] = "procedural baseline, not an Astra run"

    qj_manifest = object_manifest("QJ_")
    cr_manifest = object_manifest("CR400AF_")
    manifest = {
        "generated_by": "scripts/generate_train_models.py",
        "status": "procedural baseline; not an Astra run",
        "subjects": {
            "QJ": qj_manifest,
            "CR400AF": cr_manifest,
        },
        "requirements": {
            "independent_named_parts": True,
            "real_reference_ids_embedded": True,
            "minimum_named_parts_per_train": 10,
        },
    }
    (MODELS_DIR / "model-manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")

    bpy.ops.render.render(write_still=True)
    master_path = MODELS_DIR / "train_pair_master.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(master_path))
    save_individual("QJ_", "CR400AF_emu", MODELS_DIR / "QJ_steam_locomotive.blend", MODELS_DIR / "QJ_steam_locomotive.glb")
    save_individual("CR400AF_", "QJ_steam_locomotive", MODELS_DIR / "CR400AF_emu.blend", MODELS_DIR / "CR400AF_emu.glb")

    qj_collection = bpy.data.collections.get("QJ_steam_locomotive")
    cr_collection = bpy.data.collections.get("CR400AF_emu")
    if qj_collection:
        qj_collection.hide_viewport = False
        qj_collection.hide_render = False
    if cr_collection:
        cr_collection.hide_viewport = False
        cr_collection.hide_render = False
    bpy.ops.wm.save_as_mainfile(filepath=str(master_path))
    print("Generated QJ and CR400AF multi-part baseline assets.")


if __name__ == "__main__":
    main()
