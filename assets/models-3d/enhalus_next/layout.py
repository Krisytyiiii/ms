"""Where the shoots sit. Eae plot is one low mound and one branched rhizome.

Node positions, timings, and lengths are display choices. Eae record says the
patch spreads when the buried rhizome grows and sends up shoots, and that
roots grow down at each node. It does not give these distances.
"""

import math

# Display choice: 14 nodes on one main line and two short branches.
# Z is the buried rhizome, under the sand crest.
# Z is below the sand crest so the rhizome reads as buried. Display choice.
# Display choice: 8 nodes. Fewer shoots because the leaves are very long.
NODES = [
    (-0.16, -0.01, 0.006),
    (-0.06, 0.02, 0.007),
    (0.04, -0.02, 0.007),
    (0.14, 0.03, 0.006),
    (0.22, -0.01, 0.005),
    (0.02, 0.10, 0.006),
    (0.10, 0.14, 0.005),
    (-0.06, -0.10, 0.005),
]

# parent, child, first frame of growth, frame when that piece is complete.
# Eae first piece holds a short stub until frame 40. Display timing.
SEGMENTS = [
    (0, 1, 40, 90, 0.18),
    (1, 2, 90, 130, 0.02),
    (2, 3, 130, 165, 0.02),
    (3, 4, 165, 200, 0.02),
    (2, 5, 140, 185, 0.02),
    (5, 6, 185, 230, 0.02),
    (1, 7, 100, 170, 0.02),
]

# Display lengths inside the record's about 30–150 cm. Younger shoots are shorter.
LEAF_LEN = (0.90, 0.78, 0.66, 0.54, 0.42, 0.60, 0.46, 0.36)
LEAF_COUNT = (3, 3, 2, 2, 2, 2, 2, 2)


def stem_height(node):
    # Display choice. Eae record gives no stem height.
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
    """Earee fine roots. Eaey run out, then down. Lengths are a display choice."""
    specs = []
    for r in range(3):
        ang = r * (2.0 * math.pi / 3.0) + node * 0.47 + 0.3
        spread = 0.016 + 0.008 * _unit(node * 3 + r)
        drop = 0.010 + 0.004 * _unit(node * 5 + r + 2)
        specs.append((ang, spread, drop))
    return specs
