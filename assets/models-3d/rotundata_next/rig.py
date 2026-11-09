"""Rest pose for CR_Armature, read from the authoring curves.

Every deform bone is a direct child of one unscaled base bone.
"""

import bpy
from mathutils import Vector

from .config import CONFIG
from .util import control_points, safe_hint, set_mode

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


def rhizome_curves():
    """Main runner first, then each branch curve."""
    main = bpy.data.objects.get("CR_Rhizome")
    extra = sorted(
        (o for o in bpy.data.objects if o.name.startswith("CR_Rhizome_")),
        key=lambda o: o.name,
    )
    return [c for c in [main] + extra if c is not None]


def chain_table():
    """Bone chains for the main rhizome and each branch.

    A branch joins a node on the main runner. Its bones stay tiny until that
    node exists, then they extend across the sand.
    """
    from . import timeline

    chains = []
    bone_i = 0
    main_nseg = None
    for curve in rhizome_curves():
        nodes = rhizome_nodes(curve)
        nseg = max(0, len(nodes) - 1)
        join = int(curve.get("cr_join", -1))
        stub = join < 0
        if stub:
            ready = 40
            main_nseg = nseg
        else:
            ready = 40 if main_nseg is None else max(40, timeline.node_arrived(join, main_nseg, 40, True))
        names = ["rhizome_%02d" % (bone_i + s) for s in range(nseg)]
        chains.append({
            "curve": curve,
            "nodes": nodes,
            "bones": names,
            "join": join,
            "ready": ready,
            "stub": stub,
            "nseg": nseg,
            "bone0": bone_i,
        })
        bone_i += nseg
    return chains


def layout_bones(cfg=CONFIG):
    bones = {}
    specs = {}
    for chain in chain_table():
        nodes = chain["nodes"]
        for s, name in enumerate(chain["bones"]):
            bones[name] = (nodes[s], nodes[s + 1], UP)
            specs[name] = {
                "cr_local": s,
                "cr_count": chain["nseg"],
                "cr_ready": chain["ready"],
                "cr_stub": 1 if chain["stub"] else 0,
            }
    forward = {}
    for emp in objects_with_prefix("CR_Shoot_"):
        i = emp.name[len("CR_Shoot_"):]
        origin, stem, _side, fwd = shoot_axes(emp)
        forward[i] = fwd
        bones["shoot_" + i] = (origin, origin + stem * cfg["stem_height_m"], fwd)
    for leaf in objects_with_prefix("CR_Leaf_"):
        pts = control_points(leaf)
        key = leaf.name[len("CR_Leaf_"):]
        i = key.split("_")[0]
        bones["leaf_" + key] = (pts[0], pts[-1], forward.get(i, Vector((0.0, 1.0, 0.0))))
    for root in objects_with_prefix("CR_Root_"):
        pts = control_points(root)
        bones["root_" + root.name[len("CR_Root_"):]] = (pts[0], pts[-1], Vector((1.0, 0.0, 0.0)))
    return bones, specs


def sync_bones(arm, bones, specs=None):
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
    for name, props in (specs or {}).items():
        bone = arm.data.bones.get(name)
        if bone is None:
            continue
        for key, value in props.items():
            bone[key] = value
    base_pose = arm.pose.bones.get("base")
    if base_pose is not None:
        base_pose.location = (0.0, 0.0, 0.0)
        base_pose.rotation_euler = (0.0, 0.0, 0.0)
        base_pose.scale = (1.0, 1.0, 1.0)
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
