"""Where the shoots sit. One low mound, one rhizome, a few branches.

Positions and lengths are display choices. The record says the patch spreads
when the buried rhizome grows and sends up shoots, and that roots grow down
at each node. Leaf length stays inside "up to about 20 cm".
"""

import math

from mathutils import Vector

# Display choice: 14 nodes. The line runs the other way from the serrated-ribbon meadow.
NODES = [
    (0.160, 0.020, -0.0014),
    (0.090, -0.030, -0.0010),
    (0.020, 0.015, -0.0008),
    (-0.050, -0.020, -0.0010),
    (-0.120, 0.030, -0.0014),
    (-0.185, -0.010, -0.0018),
    (0.000, 0.090, -0.0012),
    (0.060, 0.150, -0.0016),
    (-0.020, 0.180, -0.0020),
    (-0.090, 0.120, -0.0014),
    (0.040, -0.070, -0.0012),
    (0.100, -0.130, -0.0016),
    (0.020, -0.170, -0.0020),
    (-0.070, -0.100, -0.0014),
]

# parent, child, first frame of growth, frame when that piece is complete.
SEGMENTS = [
    (0, 1, 40, 78, 0.18),
    (1, 2, 78, 108, 0.02),
    (2, 3, 108, 136, 0.02),
    (3, 4, 136, 162, 0.02),
    (4, 5, 162, 188, 0.02),
    (2, 6, 112, 142, 0.02),
    (6, 7, 142, 168, 0.02),
    (7, 8, 168, 194, 0.02),
    (7, 9, 174, 206, 0.02),
    (3, 10, 140, 170, 0.02),
    (10, 11, 170, 198, 0.02),
    (11, 12, 198, 226, 0.02),
    (4, 13, 166, 210, 0.02),
]

# Display lengths inside the record's about 7–30 cm. Younger shoots are shorter.
LEAF_LEN = (
    0.260, 0.230, 0.200, 0.170, 0.140, 0.100,
    0.210, 0.160, 0.130, 0.095,
    0.180, 0.140, 0.120, 0.095,
)
LEAF_COUNT = (3, 3, 3, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2)


def stem_height(node):
    # Display choice. The record gives no stem height. Short, so the needles are the plant.
    return 0.005 + 0.006 * (LEAF_LEN[node] / LEAF_LEN[0])


def node_axis(node):
    """Direction of the rhizome at this node, for the black scars."""
    for parent, child, _start, _end, _idle in SEGMENTS:
        if parent == node:
            return (Vector(NODES[child]) - Vector(NODES[node])).normalized()
    for parent, child, _start, _end, _idle in SEGMENTS:
        if child == node:
            return (Vector(NODES[node]) - Vector(NODES[parent])).normalized()
    return Vector((1.0, 0.0, 0.0))


def arrive_frame(node):
    if node == 0:
        return 1
    for parent, child, _start, end, _idle in SEGMENTS:
        if child == node:
            return end
    raise KeyError(node)


def shoot_window(node):
    if node == 0:
        return 1, 80, 156, 0.40, 0.22
    start = min(240, arrive_frame(node) + 12)
    stem_end = min(300, start + 64)
    leaf_end = min(300, start + 88)
    return start, stem_end, leaf_end, 0.02, 0.02


def root_window(node):
    start = 40 if node == 0 else arrive_frame(node)
    spread_end = min(300, start + 34)
    drop_end = min(300, start + 52)
    return start, spread_end, drop_end


def _unit(n):
    x = math.sin(n * 12.9898) * 43758.5453
    return x - math.floor(x)


def roots_for(node):
    """Three fine roots. They run out, then down. Lengths are a display choice."""
    specs = []
    for r in range(3):
        ang = r * (2.0 * math.pi / 3.0) + node * 0.55 + 0.4
        spread = 0.018 + 0.012 * _unit(node * 3 + r)
        drop = 0.006 + 0.003 * _unit(node * 5 + r + 2)
        specs.append((ang, spread, drop))
    return specs
