"""Spoken lines are burned along the bottom of the lesson video.

Nothing in this module builds floating 3D type. build() only clears any
caption objects left in the file.
"""


def build(frame_end=900):
    del frame_end
    from .captions import _clear

    _clear()
    print("no floating 3D text; subtitles are burned into the video")
