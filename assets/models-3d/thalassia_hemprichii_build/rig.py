"""TH_Armature rest pose, read from the Authoring curves and shoot empties.

Every deform bone is a direct child of an unscaled `base` bone. No bone inherits
a non-uniform scale, so Y-scale on one bone never shears another in glTF.
"""

import bpy
from mathutils import Vector

from .config import CONFIG
from .util import arc_table, control_points, dense_points, point_at, safe_hint, set_mode

UP = Vector((0.0, 0.0, 1.0))


def objects_with_prefix(prefix):
    return sorted((o for o in bpy.data.objects if o.name.startswith(prefix)), key=lambda o: o.name)


def rhizome_nodes(curve):
    pts = control_points(curve)
    count = int(curve.get("cr_nodes", (len(pts) + 1) // 2))
    return [pts[2 * k] for k in range(count)]


def shoot_axes(emp):
    m = emp.matrix_world
    return m.translation.copy(), m.col[2].xyz.normalized(), m.col[0].xyz.normalized(), m.col[1].xyz.normalized()


def layout_bones(cfg=CONFIG):
    """name -> (head, tail, roll hint) for every deform bone."""
    bones = {}
    nodes = rhizome_nodes(bpy.data.objects["TH_Rhizome"])
    for k in range(len(nodes) - 1):
        bones["rhizome_%02d" % k] = (nodes[k], nodes[k + 1], UP)
    forward = {}
    for emp in objects_with_prefix("TH_Shoot_"):
        i = emp.name[len("TH_Shoot_"):]
        origin, stem, _side, fwd = shoot_axes(emp)
        forward[i] = fwd
        bones["shoot_" + i] = (origin, origin + stem * cfg["stem_height_m"], fwd)
    nseg = max(1, int(cfg.get("leaf_bones", 1)))
    for curve in objects_with_prefix("TH_Leaf_"):
        key = curve.name[len("TH_Leaf_"):]
        i = key.split("_")[0]
        hint = forward.get(i, Vector((0, 1, 0)))
        dense = dense_points(curve)
        cum = arc_table(dense)
        length = max(cum[-1], 1e-6)
        cuts = [point_at(dense, cum, length * k / nseg) for k in range(nseg + 1)]
        for seg in range(nseg):
            name = "leaf_" + key if seg == 0 else "leaf_%s_s%d" % (key, seg)
            a, b = cuts[seg], cuts[seg + 1]
            if (b - a).length < 1e-4:
                b = a + Vector((0.0, 0.0, 0.012))
            bones[name] = (a, b, hint)
    for curve in objects_with_prefix("TH_Root_"):
        pts = control_points(curve)
        bones["root_" + curve.name[len("TH_Root_"):]] = (pts[0], pts[-1], Vector((1, 0, 0)))
    return bones


def sync_bones(arm, bones):
    set_mode(arm, "EDIT")
    eb = arm.data.edit_bones
    base = eb.get("base") or eb.new("base")
    base.head = (0.0, 0.0, 0.0)
    base.tail = (0.0, 0.02, 0.0)
    base.roll = 0.0
    base.use_deform = False
    for bone in list(eb):
        if bone.name != "base" and bone.name not in bones:
            eb.remove(bone)
    for name, (head, tail, hint) in bones.items():
        bone = eb.get(name) or eb.new(name)
        bone.head = head
        bone.tail = tail
        bone.align_roll(safe_hint(tail - head, hint))
        bone.parent = base
        bone.use_connect = False
        bone.inherit_scale = "FULL"
        bone.use_deform = True
    set_mode(arm, "OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
