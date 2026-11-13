"""Where the shoots sit. One low mound, one rhizome, a few branches.

Positions and lengths are display choices. The record says the patch spreads
when the buried rhizome grows and sends up shoots, and that roots grow down
at each node. Leaf length stays inside "up to about 20 cm".
"""

import math

from mathutils import Vector

# Display choice: 14 nodes. The line runs the other way from the serrated-ribbon meadow.
NODES = [
    (-0.150, 0.030, -0.0014),
    (-0.080, -0.020, -0.0010),
    (0.000, 0.025, -0.0008),
    (0.075, -0.015, -0.0010),
    (0.145, 0.035, -0.0014),
    (0.205, -0.015, -0.0018),
    (0.015, 0.100, -0.0012),
    (-0.040, 0.155, -0.0016),
    (0.045, 0.175, -0.0020),
    (0.105, 0.115, -0.0014),
    (0.010, -0.080, -0.0012),
    (-0.055, -0.140, -0.0016),
    (0.035, -0.165, -0.0020),
    (0.115, -0.095, -0.0014),
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

# Display lengths. The record says this plant is usually larger and gives no length.
# These are longer than the pinifolia display (18 cm on the longest leaf).
LEAF_LEN = (
    0.220, 0.204, 0.186, 0.170, 0.146, 0.096,
    0.182, 0.154, 0.124, 0.084,
    0.162, 0.134, 0.112, 0.076,
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
