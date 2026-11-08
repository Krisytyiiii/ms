"""rebuild_meshes(): refresh the solid Meadow meshes from the Authoring curves."""

import bpy
from mathutils import Vector

from . import geometry, rig, sand, shoot, textures
from .config import CONFIG
from .util import arc_table, collection, dense_points, link, tag


def _controls():
    c = bpy.data.objects.get("SI_Controls")
    get = (lambda k: c.get(k, CONFIG[k])) if c else (lambda k: CONFIG[k])
    return float(get("leaf_diameter_m"))


def _put(name, src, make, mats, groups_of, meadow, arm):
    obj = bpy.data.objects.get(name)
    if (src is not None and src.get("cr_hand_edited")) or (obj is not None and obj.get("cr_hand_edited")):
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
        if old.users == 0:
            bpy.data.meshes.remove(old)
    obj.vertex_groups.clear()
    for group, ids in groups.items():
        obj.vertex_groups.new(name=group).add(ids, 1.0, "REPLACE")
    mod = next((m for m in obj.modifiers if m.type == "ARMATURE"), None)
    if groups and mod is None:
        mod = obj.modifiers.new("Armature", "ARMATURE")
    if mod:
        mod.object = arm
        mod.use_vertex_groups = True
    obj.parent = arm
    obj.matrix_parent_inverse.identity()
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    return obj, True


def _whole(bone):
    def wrap(mesh):
        return mesh, {bone: list(range(len(mesh.vertices)))}

    return wrap


def rebuild_meshes(cfg=CONFIG):
    diameter = _controls()
    mats = textures.ensure_materials(int(cfg.get("vein_count", 0)))
    meadow = collection("Meadow")
    arm = bpy.data.objects["SI_Armature"]
    rig.sync_bones(arm, rig.layout_bones(cfg))
    built = 0

    rh = bpy.data.objects["SI_Rhizome"]
    dense = dense_points(rh)
    cum = arc_table(dense)
    nodes = rig.rhizome_nodes(rh)
    per = 48
    node_ds = [cum[2 * k * per] for k in range(len(nodes))]
    _o, ok = _put("Rhizome", rh, lambda: geometry.rhizome_mesh("RhizomeMesh", dense, node_ds, cfg["rhizome_radius_m"], cfg["rhizome_oval"]),
                  [mats["rhizome"]], lambda r: r, meadow, arm)
    built += ok

    path = [(p.x, p.y) for p in dense]
    _o, ok = _put("ReefSand", None, lambda: sand.build_sand("ReefSandMesh", path, cfg["sand_bottom_z"]),
                  [mats["sand"]], lambda m: (m, {}), meadow, arm)
    built += ok

    sides = {}
    for emp in rig.objects_with_prefix("SI_Shoot_"):
        i = emp.name[len("SI_Shoot_"):]
        origin, stem, side, _fwd = rig.shoot_axes(emp)
        sides[i] = side
        _o, ok = _put("Shoot_" + i, emp, lambda: shoot.shoot_mesh("ShootMesh_" + i, origin, stem, side, cfg, 16, 12),
                      [mats["stem"], mats["sheath"], mats["scar"]], _whole("shoot_" + i), meadow, arm)
        built += ok

    for curve in rig.objects_with_prefix("SI_Leaf_"):
        key = curve.name[len("SI_Leaf_"):]
        side = sides.get(key.split("_")[0]) or Vector((1.0, 0.0, 0.0))
        leaf_d = float(curve.get("si_diameter_m", diameter))
        pts = dense_points(curve)
        mat = mats["young"] if curve.get("cr_young") else mats["leaf"]
        twist = float(curve.get("cr_twist", 0.0))
        _o, ok = _put(
            "Leaf_" + key,
            curve,
            lambda leaf_d=leaf_d, twist=twist, pts=pts, side=side, key=key: geometry.leaf_mesh(
                "LeafMesh_" + key, pts, leaf_d, side, twist, body_rings=10, sides=24
            ),
            [mat],
            _whole("leaf_" + key),
            meadow,
            arm,
        )
        built += ok

    for curve in rig.objects_with_prefix("SI_Root_"):
        key = curve.name[len("SI_Root_"):]
        pts = dense_points(curve, 16)
        _o, ok = _put("Root_" + key, curve, lambda: geometry.root_mesh("RootMesh_" + key, pts, cfg["root_radius_m"], rings=5),
                      [mats["root"]], _whole("root_" + key), meadow, arm)
        built += ok
    print("rebuild_meshes: refreshed", built, "meshes")
    return built
