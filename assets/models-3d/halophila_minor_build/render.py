"""Render the aquarium growth clip and preview stills from the camera."""

import os
import shutil

import bpy

SPECIES_DIR = r"d:\pepot\marinesee\assets\models-3d\halophila_minor"
APP_DIR = r"d:\pepot\marinesee\app\assets\models-3d"
SILENT_MP4 = SPECIES_DIR + r"\halophila_minor_lesson_silent.mp4"
LESSON_MP4 = SPECIES_DIR + r"\halophila_minor_lesson.mp4"
APP_LESSON_MP4 = APP_DIR + r"\halophila_minor_lesson.mp4"


def _frame(scene, width, height, samples):
    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = int(samples)
    except AttributeError:
        pass


def render_stills(out_dir, frames=(1, 120, 200, 300), width=1280, height=720, samples=16):
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    _frame(scene, width, height, samples)
    scene.render.use_persistent_data = True
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 92
    saved = []
    for f in frames:
        scene.frame_set(f)
        fp = os.path.join(out_dir, "aquarium_f%03d.jpg" % f)
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        saved.append(fp)
    return saved


def render_clip(out_path=SILENT_MP4, also_copy=False, frame_end=None, width=1280, height=720, samples=16):
    scene = bpy.context.scene
    _frame(scene, width, height, samples)
    scene.frame_start = 1
    if frame_end is not None:
        scene.frame_end = int(frame_end)
    scene.render.fps = 30
    scene.render.use_persistent_data = False

    media = [i.identifier for i in scene.render.image_settings.bl_rna.properties["media_type"].enum_items]
    if "VIDEO" in media:
        scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    ff = scene.render.ffmpeg
    containers = [i.identifier for i in ff.bl_rna.properties["format"].enum_items]
    codecs = [i.identifier for i in ff.bl_rna.properties["codec"].enum_items]
    ff.format = "MPEG4" if "MPEG4" in containers else containers[0]
    ff.codec = "H264" if "H264" in codecs else codecs[0]
    if "constant_rate_factor" in ff.bl_rna.properties:
        rates = [i.identifier for i in ff.bl_rna.properties["constant_rate_factor"].enum_items]
        if "MEDIUM" in rates:
            ff.constant_rate_factor = "MEDIUM"
    scene.render.filepath = out_path
    bpy.ops.render.render(animation=True)
    if also_copy:
        if os.path.abspath(out_path) != os.path.abspath(APP_LESSON_MP4):
            shutil.copy2(out_path, APP_LESSON_MP4)
    print("RENDER_DONE", out_path)
    return out_path




def _eevee(scene):
    engines = [item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items]
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        if name in engines:
            scene.render.engine = name
            return name
    return scene.render.engine


def render_lesson(frame_end=900):
    """Thirty seconds, 1920x1080. Silent picture; speech is muxed afterwards."""
    scene = bpy.context.scene
    _eevee(scene)
    return render_clip(
        out_path=SILENT_MP4,
        also_copy=False,
        frame_end=frame_end,
        width=1920,
        height=1080,
        samples=8,
    )


def render_timelapse(frame_end=1800):
    raise RuntimeError("Halophila minor does not ship a growth clip")
