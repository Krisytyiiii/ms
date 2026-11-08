"""Lesson camera. It turns one leaf from the side to the end. No title cards."""

import json
import os

import bpy
from mathutils import Quaternion, Vector

from .script import TIMINGS
from .util import arc_table, dense_points, point_at


def _cues():
    if not os.path.isfile(TIMINGS):
        return [
            {"text": "This is noodle seagrass, Syringodium isoetifolium.", "start": 0.0, "end": 4.0},
            {"text": "A display, not a scan of a meadow in Mati.", "start": 4.4, "end": 8.0},
            {"text": "Turn the plant.", "start": 8.8, "end": 10.2},
            {"text": "The leaf stays round.", "start": 10.6, "end": 13.4},
            {"text": "It is not a flat strap.", "start": 13.8, "end": 16.0},
            {"text": "The tip tapers to a point, the way a piece of spaghetti does.", "start": 16.4, "end": 20.4},
            {"text": "The leaves are about 7 to 30 centimetres long.", "start": 21.0, "end": 24.0},
            {"text": "The patch spreads when the buried stem grows through the sand and sends up new shoots.", "start": 24.3, "end": 27.2},
            {"text": "Roots grow down at each node.", "start": 27.5, "end": 29.0},
            {"text": "It can also flower and set seed.", "start": 29.2, "end": 30.0},
        ]
    with open(TIMINGS, "r", encoding="utf-8") as handle:
        return json.load(handle)["cues"]


def _when(cues, snippet, default):
    for cue in cues:
        if snippet in cue["text"]:
            return float(cue["start"])
    return default


def _hero():
    heroes = [obj for obj in bpy.data.objects if obj.type == "CURVE" and obj.get("cr_hero")]
    if not heroes:
        raise RuntimeError("hero leaf curve is missing")
    pts = dense_points(heroes[0])
    return pts


def _open_side(tangent, tip, center):
    """Camera side that faces open water, away from the middle of the stand."""
    side = tangent.cross(Vector((0.0, 0.0, 1.0)))
    if side.length < 1e-6:
        side = Vector((1.0, 0.0, 0.0))
    side.normalize()
    away = Vector((tip.x - center.x, tip.y - center.y, 0.0))
    if away.length < 1e-6:
        away = Vector((1.0, -0.4, 0.0))
    if side.dot(away) < 0.0:
        side = -side
    return side.normalized()


def _slerp(a, b, pivot, t):
    va = a - pivot
    vb = b - pivot
    if va.length < 1e-8 or vb.length < 1e-8:
        return a.lerp(b, t)
    axis = va.cross(vb)
    if axis.length < 1e-8:
        return a.lerp(b, t)
    axis.normalize()
    ang = va.angle(vb)
    turned = Quaternion(axis, ang * t) @ va
    turned.length = va.length + (vb.length - va.length) * t
    return pivot + turned


def _look(cam, frame, eye, aim, lens):
    cam.location = eye
    cam.rotation_euler = (aim - eye).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=frame)
    cam.keyframe_insert("rotation_euler", frame=frame)
    cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=frame)


def _linear(obj):
    from .grow import fcurves

    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return
    for fc in fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = "AUTO_CLAMPED"
            kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()


def frame_camera(cam):
    """Side view, then the end of the same leaf, so the circle and the point both show."""
    for constraint in list(cam.constraints):
        cam.constraints.remove(constraint)
    if cam.animation_data:
        cam.animation_data_clear()
    if cam.data.animation_data:
        cam.data.animation_data_clear()

    pts = _hero()
    cum = arc_table(pts)
    length = cum[-1]
    tip = pts[-1]
    tangent = (tip - point_at(pts, cum, length * 0.72)).normalized()
    shoots = [obj.matrix_world.translation.copy() for obj in bpy.data.objects if obj.name.startswith("SI_Shoot_")]
    center = sum(shoots, Vector()) / len(shoots)
    side = _open_side(tangent, tip, center)
    # Front-right of the tip, in open water, so the round shaft and the point are clear of the stand.
    aim_side = tip + Vector((-0.015, 0.008, -0.055))
    eye_side = tip + Vector((0.16, -0.22, -0.005))
    aim_end = tip + Vector((-0.012, 0.006, -0.035))
    eye_end = tip + Vector((0.042, -0.050, 0.042))

    meadow_aim = Vector((center.x, center.y, 0.09))
    meadow_eye = meadow_aim + Vector((0.02, -0.70, 0.16))
    length_aim = Vector((center.x, center.y, 0.08))
    length_eye = length_aim + Vector((0.10, -0.46, 0.08))
    cut = [p for p in shoots if p.y < -0.02]
    cut_at = (sum(cut, Vector()) / len(cut)) if cut else center
    cut_aim = Vector((cut_at.x, cut_at.y, cut_at.z - 0.008))
    cut_eye = cut_aim + Vector((0.0, -0.24, 0.012))
    root_eye = cut_aim + Vector((0.02, -0.18, 0.006))

    cues = _cues()
    turn = _when(cues, "Turn the plant", 8.0)
    round_at = _when(cues, "The leaf stays round", 10.5)
    strap = _when(cues, "flat strap", 13.5)
    tip_at = _when(cues, "The tip tapers", 16.0)
    lengths = _when(cues, "7 to 30", 20.5)
    patch = _when(cues, "The patch spreads", 23.5)
    roots = _when(cues, "Roots grow", 26.5)
    flower = _when(cues, "flower", 28.2)

    def frame(second):
        return max(1, min(900, int(round(second * 30)) + 1))

    _look(cam, 1, meadow_eye, meadow_aim, 46)
    _look(cam, frame(turn), meadow_eye, meadow_aim, 46)
    _look(cam, frame(round_at), eye_side, aim_side, 58)
    _look(cam, frame(strap + 0.35), eye_side, aim_side, 58)
    _look(cam, frame(tip_at), _slerp(eye_side, eye_end, tip, 0.35), aim_side.lerp(aim_end, 0.35), 70)
    _look(cam, frame(tip_at + 1.15), eye_end, aim_end, 70)
    hold_end = min(lengths - 0.15, tip_at + 2.4)
    _look(cam, frame(hold_end), eye_end, aim_end, 70)
    _look(cam, frame(lengths + 0.35), length_eye, length_aim, 44)
    _look(cam, frame(patch), length_eye, length_aim, 44)
    _look(cam, frame(patch + 0.7), cut_eye, cut_aim, 52)
    _look(cam, frame(roots + 0.25), root_eye, cut_aim + Vector((0.0, 0.0, -0.004)), 58)
    _look(cam, frame(flower), meadow_eye, meadow_aim, 46)
    _look(cam, 900, meadow_eye, meadow_aim, 46)

    marks = {
        "side": frame(round_at),
        "end": frame(tip_at + 1.15),
        "length": frame(lengths + 0.35),
        "cut": frame(patch + 0.7),
        "roots": frame(roots + 0.25),
    }
    _linear(cam)
    if cam.data.animation_data:
        _linear(cam.data)
    cam.data.clip_start = 0.002
    cam.data.clip_end = 30
    fits = [item.identifier for item in cam.data.bl_rna.properties["sensor_fit"].enum_items]
    if "HORIZONTAL" in fits:
        cam.data.sensor_fit = "HORIZONTAL"
    bpy.context.scene.camera = cam
    print("lesson camera", marks)
    return marks
