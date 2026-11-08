"""rebuild_meshes(): refresh the solid Meadow meshes from the Authoring curves."""

import bpy
from mathutils import Vector

from . import geometry, rig, sand, shoot, textures
from .config import CONFIG
from .util import arc_table, collection, dense_points, link, tag


def _controls():
    c = bpy.data.objects.get("TH_Controls")
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


def _segment_groups(mesh, bone_prefix, nseg):
    """One full-weight bone per vertex, split along the leaf so a curve can grow."""
    uv_data = mesh.uv_layers["UVMap"].data
    acc = [0.0] * len(mesh.vertices)
    cnt = [0] * len(mesh.vertices)
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            acc[vi] += uv_data[li].uv.y
            cnt[vi] += 1
    groups = {}
    nseg = max(1, int(nseg))
    for vi, (total, count) in enumerate(zip(acc, cnt)):
        v = (total / count) if count else 0.0
        seg = min(nseg - 1, max(0, int(min(0.9999, v) * nseg)))
        name = bone_prefix if seg == 0 else "%s_s%d" % (bone_prefix, seg)
        groups.setdefault(name, []).append(vi)
    return mesh, groups


def rebuild_meshes(cfg=CONFIG):
    width, thickness, veins = _controls()
    mats = textures.ensure_materials(veins)
    meadow = collection("Meadow")
    arm = bpy.data.objects["TH_Armature"]
    rig.sync_bones(arm, rig.layout_bones(cfg))
    built = 0

    rh = bpy.data.objects["TH_Rhizome"]
    dense = dense_points(rh)
    cum = arc_table(dense)
    nodes = rig.rhizome_nodes(rh)
    per = 48
    node_ds = [cum[2 * k * per] for k in range(len(nodes))]
    _o, ok = _put("Rhizome", rh, lambda: geometry.rhizome_mesh("RhizomeMesh", dense, node_ds, cfg["rhizome_radius_m"], cfg["rhizome_oval"]),
                  [mats["rhizome"]], lambda r: r, meadow, arm)
    built += ok
    half = float(cfg.get("rhizome_scar_half_m", 0.00115))
    _o, ok = _put(
        "RhizomeScars",
        None,
        lambda: geometry.scar_bands("RhizomeScarMesh", dense, node_ds, cfg["rhizome_radius_m"], half),
        [mats["scar"]],
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
    for emp in rig.objects_with_prefix("TH_Shoot_"):
        i = emp.name[len("TH_Shoot_"):]
        origin, stem, side, _fwd = rig.shoot_axes(emp)
        sides[i] = side
        stem_sides, arc = (8, 8) if cfg.get("variant") == "lesson" else (10, 12)
        _o, ok = _put("Shoot_" + i, emp, lambda s=stem_sides, a=arc: shoot.shoot_mesh("ShootMesh_" + i, origin, stem, side, cfg, s, a),
                      [mats["stem"], mats["sheath"], mats["scar"]], _whole("shoot_" + i), meadow, arm)
        built += ok

    for curve in rig.objects_with_prefix("TH_Leaf_"):
        key = curve.name[len("TH_Leaf_"):]
        side = sides.get(key.split("_")[0]) or Vector((1.0, 0.0, 0.0))
        w = float(curve.get("th_width_m", curve.get("cr_width_m", width)))
        t = float(curve.get("th_thickness_m", curve.get("cr_thickness_m", thickness)))
        pts = dense_points(curve)
        mat = mats["young"] if curve.get("cr_young") else mats["leaf"]
        rings = 14
        plane = Vector((
            float(curve.get("cr_px", 0.0)),
            float(curve.get("cr_py", 1.0)),
            float(curve.get("cr_pz", 0.0)),
        ))
        nseg = max(1, int(cfg.get("leaf_bones", 1)))
        _o, ok = _put(
            "Leaf_" + key,
            curve,
            lambda n=rings, plane=plane: geometry.leaf_mesh(
                "LeafMesh_" + key, pts, w, t, veins, side, float(curve.get("cr_twist", 0.0)),
                cfg["vein_groove_m"], cfg["leaf_crown_m"], body_rings=n, plane=plane,
            ),
            [mat],
            lambda mesh, prefix="leaf_" + key, nseg=nseg: _segment_groups(mesh, prefix, nseg),
            meadow,
            arm,
        )
        built += ok

    for curve in rig.objects_with_prefix("TH_Root_"):
        key = curve.name[len("TH_Root_"):]
        pts = dense_points(curve, 16)
        root_rings = 4 if cfg.get("variant") == "lesson" else 6
        _o, ok = _put("Root_" + key, curve, lambda n=root_rings: geometry.root_mesh("RootMesh_" + key, pts, cfg["root_radius_m"], rings=n),
                      [mats["root"]], _whole("root_" + key), meadow, arm)
        built += ok
    print("rebuild_meshes: refreshed", built, "meshes")
    return built
