"""rebuild_meshes(): refresh Meadow from the authoring curves without moving those curves."""

import bpy

from . import geometry, rig, sand, shoot, textures
from .config import CONFIG
from .util import arc_table, collection, dense_points, link, tag


def _controls(cfg):
    ctrl = bpy.data.objects.get("CR_Controls")
    if ctrl is None:
        return float(cfg["leaf_width_m"]), int(cfg["vein_count"])
    return float(ctrl.get("leaf_width_m", cfg["leaf_width_m"])), int(ctrl.get("vein_count", cfg["vein_count"]))


def _put(name, src, make, mats, groups_of, meadow, arm):
    obj = bpy.data.objects.get(name)
    kept = obj is not None and (
        (src is not None and src.get("cr_hand_edited")) or obj.get("cr_hand_edited")
    )
    if kept:
        return obj, False
    mesh, groups = groups_of(make())
    for mat in mats:
        mesh.materials.append(mat)
    if obj is None:
        obj = bpy.data.objects.new(name, mesh)
        link(obj, meadow)
        tag(obj)
    else:
        old = obj.data
        obj.data = mesh
        if old and old.users == 0:
            bpy.data.meshes.remove(old)
        link(obj, meadow)
    if obj.animation_data:
        obj.animation_data_clear()
    obj.vertex_groups.clear()
    for group, ids in groups.items():
        if ids:
            obj.vertex_groups.new(name=group).add(ids, 1.0, "REPLACE")
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    if groups:
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        mod.use_vertex_groups = True
        obj.parent = arm
        obj.matrix_parent_inverse.identity()
    else:
        obj.parent = None
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.hide_render = False
    if src is not None and src.get("cr_hero"):
        obj["cr_hero"] = 1
    elif "cr_hero" in obj.keys():
        del obj["cr_hero"]
    return obj, True


def _whole(bone):
    def wrap(mesh):
        return mesh, {bone: list(range(len(mesh.vertices)))}

    return wrap


def _none(mesh):
    return mesh, {}


def rebuild_meshes(cfg=CONFIG):
    width, veins = _controls(cfg)
    mats = textures.ensure_materials(veins)
    meadow = collection("Meadow")
    arm = bpy.data.objects["CR_Armature"]
    bones, specs = rig.layout_bones(cfg)
    rig.sync_bones(arm, bones, specs)
    action = bpy.data.actions.get("Grow")
    if action is not None and arm.animation_data:
        arm.animation_data.action = action
    built = 0
    thickness = float(cfg["leaf_thickness_m"])
    shoulder = float(cfg["leaf_shoulder"])

    rh_curves = rig.rhizome_curves()
    paths = []
    xy = []
    for chain_i, curve in enumerate(rh_curves):
        dense = dense_points(curve, 16)
        cum = arc_table(dense)
        nodes = rig.rhizome_nodes(curve)
        per = 16
        node_ds = [cum[min(len(cum) - 1, 2 * k * per)] for k in range(len(nodes))]
        bone0 = 0
        for earlier in rh_curves[:chain_i]:
            bone0 += max(0, int(earlier.get("cr_nodes", 1)) - 1)
        mesh_name = "Rhizome" if chain_i == 0 else "Rhizome_%02d" % chain_i
        _obj, ok = _put(
            mesh_name,
            curve,
            lambda d=dense, nd=node_ds, b0=bone0, taper=chain_i == 0: geometry.rhizome_mesh(
                mesh_name + "Mesh", d, nd, cfg["rhizome_radius_m"], cfg["rhizome_oval"], b0, taper
            ),
            [mats["rhizome"]],
            lambda made: made,
            meadow,
            arm,
        )
        built += ok
        paths.append([(p.x, p.y) for p in dense])
        xy.extend((p.x, p.y) for p in nodes)
    _obj, ok = _put(
        "Sand",
        None,
        lambda: sand.build_sand("SandMesh", xy, paths, cfg),
        [mats["sand"]],
        _none,
        meadow,
        arm,
    )
    built += ok

    sides = {}
    for emp in rig.objects_with_prefix("CR_Shoot_"):
        i = emp.name[len("CR_Shoot_"):]
        origin, stem, side, _fwd = rig.shoot_axes(emp)
        sides[i] = side
        _obj, ok = _put(
            "Shoot_" + i,
            emp,
            lambda o=origin, s=stem, sd=side: shoot.shoot_mesh("ShootMesh_" + i, o, s, sd, cfg),
            [mats["stem"], mats["sheath"], mats["scar"]],
            _whole("shoot_" + i),
            meadow,
            arm,
        )
        built += ok

    for curve in rig.objects_with_prefix("CR_Leaf_"):
        key = curve.name[len("CR_Leaf_"):]
        side = sides.get(key.split("_")[0])
        if side is None:
            side = curve.matrix_world.col[0].xyz
        w = float(curve.get("cr_width_m", width))
        pts = dense_points(curve, 16)
        mat = mats["young"] if curve.get("cr_young") else mats["leaf"]
        twist = float(curve.get("cr_twist", 0.0))
        _obj, ok = _put(
            "Leaf_" + key,
            curve,
            lambda p=pts, ww=w, sd=side, tw=twist: geometry.leaf_mesh(
                "LeafMesh_" + key, p, ww, thickness, sd, tw, shoulder
            ),
            [mat],
            _whole("leaf_" + key),
            meadow,
            arm,
        )
        built += ok

    for curve in rig.objects_with_prefix("CR_Root_"):
        key = curve.name[len("CR_Root_"):]
        pts = dense_points(curve, 8)
        _obj, ok = _put(
            "Root_" + key,
            curve,
            lambda p=pts: geometry.root_mesh("RootMesh_" + key, p, cfg["root_radius_m"]),
            [mats["root"]],
            _whole("root_" + key),
            meadow,
            arm,
        )
        built += ok
    bpy.context.view_layer.update()
    print("rebuild_meshes: refreshed", built, "meshes")
    return built
