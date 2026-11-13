"""Where the shoots sit. The plot is one low mound and one branched rhizome.

Node positions, timings, and lengths are display choices. The record says the
patch spreads when the buried rhizome grows and sends up shoots, and that
roots grow down at each node. It does not give these distances.
"""

import math

# Display choice: 14 nodes on one main line and two short branches.
# Z is the buried rhizome, under the sand crest.
# Z is below the sand crest so the rhizome reads as buried. Display choice.
NODES = [
    (-0.170, -0.012, -0.0020),
    (-0.088, 0.018, -0.0014),
    (-0.006, -0.016, -0.0010),
    (0.078, 0.022, -0.0012),
    (0.156, -0.008, -0.0018),
    (0.224, 0.042, -0.0022),
    (-0.062, 0.072, -0.0016),
    (0.018, 0.108, -0.0018),
    (0.104, 0.078, -0.0020),
    (0.012, 0.150, -0.0024),
    (0.036, -0.070, -0.0018),
    (-0.050, -0.100, -0.0022),
    (-0.130, -0.058, -0.0024),
    (0.112, -0.104, -0.0024),
]

# parent, child, first frame of growth, frame when that piece is complete.
# The first piece holds a short stub until frame 40. Display timing.
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

# Display choice: mature straps longer, tip shoots shorter. Not in the record.
# Display lengths inside the record's about 10–40 cm.
LEAF_LEN = (
    0.280, 0.250, 0.220, 0.190, 0.160, 0.120,
    0.230, 0.180, 0.150, 0.120,
    0.200, 0.160, 0.140, 0.120,
)
LEAF_COUNT = (4, 4, 3, 3, 3, 2, 4, 3, 3, 2, 3, 3, 2, 2)


def stem_height(node):
    # Display choice. The record gives no stem height.
    return 0.012 + 0.010 * (LEAF_LEN[node] / LEAF_LEN[0])


def arrive_frame(node):
    if node == 0:
        return 1
    for parent, child, _start, end, _idle in SEGMENTS:
        if child == node:
            return end
    raise KeyError(node)


def shoot_window(node):
    """Frames for the stem, then the frame the leaves finish."""
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
        ang = r * (2.0 * math.pi / 3.0) + node * 0.47 + 0.3
        spread = 0.022 + 0.014 * _unit(node * 3 + r)
        drop = 0.006 + 0.003 * _unit(node * 5 + r + 2)
        specs.append((ang, spread, drop))
    return specs
