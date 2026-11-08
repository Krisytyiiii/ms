"""Render the aquarium growth clip and preview stills from the camera."""

import os
import shutil

import bpy

LESSON_MP4 = r"d:\pepot\marinesee\assets\models-3d\thalassia_hemprichii\video\thalassia_hemprichii_lesson.mp4"
RENDER_MP4 = LESSON_MP4
ASSETS_MP4 = LESSON_MP4
APP_MP4 = r"d:\pepot\marinesee\app\assets\models-3d\thalassia_hemprichii_lesson.mp4"
TIMELAPSE_MP4 = LESSON_MP4
SILENT_MP4 = r"C:\Users\reaga\AppData\Local\Temp\th_hemprichii_lesson_silent.mp4"


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


def render_clip(out_path=RENDER_MP4, also_copy=False, frame_end=None, width=1280, height=720, samples=16):
    if "rotundata" in os.path.abspath(out_path).replace("\\", "/").lower():
        raise RuntimeError("refusing to write a rotundata path: " + out_path)
    scene = bpy.context.scene
    _frame(scene, width, height, samples)
    scene.frame_start = 1
    if frame_end is not None:
        scene.frame_end = int(frame_end)
    scene.render.fps = 30
    scene.render.use_persistent_data = True

    media = [i.identifier for i in scene.render.image_settings.bl_rna.properties["media_type"].enum_items]
    if "VIDEO" in media:
        scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    ff = scene.render.ffmpeg
    containers = [i.identifier for i in ff.bl_rna.properties["format"].enum_items]
    codecs = [i.identifier for i in ff.bl_rna.properties["codec"].enum_items]
    ff.format = "MPEG4" if "MPEG4" in containers else containers[0]
    ff.codec = "H264" if "H264" in codecs else codecs[0]
    if "audio_codec" in ff.bl_rna.properties:
        audio = [i.identifier for i in ff.bl_rna.properties["audio_codec"].enum_items]
        if "NONE" in audio:
            ff.audio_codec = "NONE"
    if "constant_rate_factor" in ff.bl_rna.properties:
        rates = [i.identifier for i in ff.bl_rna.properties["constant_rate_factor"].enum_items]
        if "MEDIUM" in rates:
            ff.constant_rate_factor = "MEDIUM"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scene.render.filepath = out_path
    bpy.ops.render.render(animation=True)
    if also_copy:
        for target in (ASSETS_MP4, APP_MP4):
            if os.path.abspath(out_path) != os.path.abspath(target):
                shutil.copy2(out_path, target)
    print("RENDER_DONE", out_path)
    return out_path


def _eevee(scene):
    engines = [item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items]
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        if name in engines:
            scene.render.engine = name
            return name
    return scene.render.engine


def prepare_picture(scene):
    """Eevee without raytracing or subsurface, so the 900-frame film can finish."""
    engine = _eevee(scene)
    ee = getattr(scene, "eevee", None)
    if ee is not None and hasattr(ee, "use_raytracing"):
        ee.use_raytracing = False
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        bsdf = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        for name in ("Subsurface Weight", "Subsurface"):
            sock = bsdf.inputs.get(name)
            if sock is not None and not sock.is_linked:
                sock.default_value = 0.0
    print("PICTURE", engine, "raytracing off, subsurface off")
    return engine


def render_lesson(frame_end=900):
    """Silent 30-second 1920x1080 picture. Speech is muxed afterwards."""
    scene = bpy.context.scene
    prepare_picture(scene)
    return render_clip(
        out_path=SILENT_MP4,
        also_copy=False,
        frame_end=frame_end,
        width=1920,
        height=1080,
        samples=4,
    )


def render_timelapse(frame_end=1800):
    """Minute clip only. Does not replace the aquarium film or the phone model."""
    return render_clip(
        out_path=TIMELAPSE_MP4,
        also_copy=False,
        frame_end=frame_end,
        width=1920,
        height=1080,
        samples=24,
    )
