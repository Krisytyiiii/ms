"""rebuild_meshes(): refresh the solid Meadow meshes from the Authoring curves."""

import bpy
from mathutils import Vector

from . import geometry, geometry_shapes, rig, sand, shoot, textures
from .config import CONFIG, oname
from .util import arc_table, collection, dense_points, link, tag


def _controls():
    c = bpy.data.objects.get(oname("Controls"))
    get = (lambda k: c.get(k, CONFIG[k])) if c else (lambda k: CONFIG[k])
    return float(get("leaf_width_m")), float(get("leaf_thickness_m")), int(get("vein_count"))


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
    width, thickness, veins = _controls()
    mats = textures.ensure_materials(veins)
    meadow = collection("Meadow")
    arm = bpy.data.objects[oname("Armature")]
    rig.sync_bones(arm, rig.layout_bones(cfg))
    built = 0

    rh = bpy.data.objects[oname("Rhizome")]
    dense = dense_points(rh)
    cum = arc_table(dense)
    nodes = rig.rhizome_nodes(rh)
    per = 48
    node_ds = [cum[2 * k * per] for k in range(len(nodes))]
    _o, ok = _put(
        "Rhizome",
        rh,
        lambda: geometry.rhizome_mesh(
            "RhizomeMesh", dense, node_ds, cfg["rhizome_radius_m"], cfg["rhizome_oval"], step=0.008, sides=6
        ),
        [mats["rhizome"]],
        lambda r: r,
        meadow,
        arm,
    )
    built += ok
    if cfg.get("rhizome_scars"):
        _o, ok = _put(
            "RhizomeScars",
            None,
            lambda: geometry_shapes.scar_bands("RhizomeScarMesh", dense, node_ds, cfg["rhizome_radius_m"]),
            [mats["scar"]],
            lambda r: r,
            meadow,
            arm,
        )
        built += ok
    if cfg.get("rhizome_bristles"):
        _o, ok = _put(
            "RhizomeBristles",
            None,
            lambda: geometry_shapes.bristle_mesh("RhizomeBristleMesh", dense, node_ds, cfg["rhizome_radius_m"]),
            [mats["bristle"]],
            lambda r: r,
            meadow,
            arm,
        )
        built += ok

    path = [(p.x, p.y) for p in dense]
    _o, ok = _put("ReefSand", None, lambda: sand.build_sand("ReefSandMesh", path, cfg["sand_bottom_z"]),
                  [mats["sand"]], lambda m: (m, {}), meadow, arm)
    built += ok

    sides = {}
    shoot_prefix = oname("Shoot_")
    for emp in rig.objects_with_prefix(shoot_prefix):
        i = emp.name[len(shoot_prefix):]
        origin, stem, side, _fwd = rig.shoot_axes(emp)
        sides[i] = side
        _o, ok = _put(
            "Shoot_" + i,
            emp,
            lambda o=origin, s=stem, sd=side: shoot.shoot_mesh("ShootMesh_" + i, o, s, sd, cfg, 16, 8),
            [mats["stem"], mats["sheath"], mats["scar"]],
            _whole("shoot_" + i),
            meadow,
            arm,
        )
        built += ok

    for curve in rig.objects_with_prefix("CS_Leaf_"):
        key = curve.name[len("CS_Leaf_"):]
        side = sides.get(key.split("_")[0]) or Vector((1.0, 0.0, 0.0))
        w = float(curve.get("cr_width_m", width))
        t = float(curve.get("cr_thickness_m", thickness))
        pts = dense_points(curve)
        mat = mats["young"] if curve.get("cr_young") else mats["leaf"]
        _o, ok = _put(
            "Leaf_" + key,
            curve,
            lambda c=curve, ww=w, tt=t, sd=side: geometry_shapes.serrated_strap_mesh(
                "LeafMesh_" + key,
                dense_points(c),
                ww,
                tt,
                sd,
                float(c.get("cr_twist", 0.0)),
                cfg["leaf_crown_m"],
            ),
            [mat],
            _whole("leaf_" + key),
            meadow,
            arm,
        )
        built += ok

    for curve in rig.objects_with_prefix("CS_Root_"):
        key = curve.name[len("CS_Root_"):]
        pts = dense_points(curve, 12)
        _o, ok = _put(
            "Root_" + key,
            curve,
            lambda p=pts: geometry.root_mesh("RootMesh_" + key, p, cfg["root_radius_m"], rings=5, sides=4),
            [mats["root"]],
            _whole("root_" + key),
            meadow,
            arm,
        )
        built += ok
    print("rebuild_meshes: refreshed", built, "meshes")
    return built
