"""Locked growth windows, frames 1-330.

What happens inside a window is a display choice. The windows themselves are not.
Frame 330 is not a growth frame: the caller copies frame 1 onto it.
"""

# Display choices for how small the bud is inside frames 1-40.
STUB = 0.42
SHORT_STEM = 0.36
SHORT_LEAF = 0.24
# Display choice. Waiting shoots sit this far under their node, inside the mound.
TUCK_Z = 0.018


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def ramp(frame, start, end, low, high=1.0, linear=False):
    if frame <= start:
        return low
    if frame >= end:
        return high
    u = (frame - start) / max(1.0, float(end - start))
    if not linear:
        u = smoothstep(u)
    return low + (high - low) * u


def segment_window(local_i, local_n, ready, end=120):
    """Frames when one rhizome segment starts and finishes."""
    local_n = max(1, int(local_n))
    span = end - ready
    a = ready + round(span * local_i / local_n)
    b = ready + round(span * (local_i + 1) / local_n)
    if b <= a:
        b = a + 1
    return a, b


def segment_scale(local_i, local_n, frame, tiny, ready=40, stub_first=False, end=120):
    """Length of one segment. The first segment of the main runner starts as a stub."""
    a, b = segment_window(local_i, local_n, ready, end)
    low = STUB if stub_first and local_i == 0 else tiny
    return ramp(frame, a, b, low, 1.0, linear=True)


def rhizome_scale(i, nseg, frame, tiny):
    return segment_scale(i, nseg, frame, tiny, ready=40, stub_first=True)


def node_arrived(node_index, local_n, ready, stub_first=False, end=120):
    """Frame when a node on a runner exists."""
    if node_index <= 0:
        return 1 if stub_first else ready
    return segment_window(node_index - 1, local_n, ready, end)[1]


def root_scale_at(frame, tiny, ready):
    return ramp(frame, ready, min(300, int(ready) + 42), tiny, 1.0, linear=False)


def root_window(i, nseg):
    """A root starts only after its node exists, and not before frame 40."""
    ready = 40 if i <= 0 else node_arrived(i, nseg, 40, stub_first=True)
    return max(40, ready), min(300, max(40, ready) + 42)


def first_wave(count):
    """Display choice: about half the shoots, including the bud, rise in frames 120-200."""
    return max(1, int(count) // 2)


def shoot_window(i, count):
    first = first_wave(count)
    if i < first:
        if first == 1:
            return 120, 200
        start = 120 + round(i * 48 / (first - 1))
        end = 200 if i == first - 1 else min(200, start + 52)
        return start, end
    rest = count - first
    j = i - first
    if rest <= 1:
        return 200, 300
    start = 200 + round(j * 56 / (rest - 1))
    end = 300 if j == rest - 1 else min(300, start + 58)
    return start, max(start + 12, end)


def leaf_window(i, j, count):
    start, end = shoot_window(i, count)
    begin = start + j * 3
    return min(begin, end - 8), end


def shoot_scale(i, count, frame, tiny):
    start, end = shoot_window(i, count)
    low = SHORT_STEM if i == 0 else tiny
    return ramp(frame, start, end, low, 1.0, linear=False)


def leaf_scale(i, j, count, frame, tiny):
    start, end = leaf_window(i, j, count)
    low = SHORT_LEAF if i == 0 else tiny
    return ramp(frame, start, end, low, 1.0, linear=False)


def leaf_open(i, j, count, frame):
    start, end = leaf_window(i, j, count)
    return ramp(frame, start, end, 0.0, 1.0, linear=False)


def root_scale(i, nseg, frame, tiny):
    start, end = root_window(i, nseg)
    return ramp(frame, start, end, tiny, 1.0, linear=False)


def tuck(i, count, frame):
    """1 while a later shoot is still waiting, 0 when it has risen."""
    if i == 0:
        return 0.0
    start, end = shoot_window(i, count)
    return 1.0 - ramp(frame, start, end, 0.0, 1.0, linear=False)


def self_check(count=14, tiny=0.02):
    nseg = count - 1
    assert abs(rhizome_scale(0, nseg, 1, tiny) - STUB) < 1e-6
    assert rhizome_scale(nseg - 1, nseg, 1, tiny) == tiny
    assert rhizome_scale(0, nseg, 40, tiny) == STUB
    for i in range(nseg):
        assert rhizome_scale(i, nseg, 120, tiny) == 1.0
        assert rhizome_scale(i, nseg, 300, tiny) == 1.0
    assert abs(shoot_scale(0, count, 1, tiny) - SHORT_STEM) < 1e-6
    assert abs(shoot_scale(0, count, 120, tiny) - SHORT_STEM) < 1e-6
    assert shoot_scale(count - 1, count, 1, tiny) == tiny
    assert shoot_scale(count - 1, count, 120, tiny) == tiny
    first = first_wave(count)
    for i in range(first):
        assert shoot_scale(i, count, 200, tiny) == 1.0
    assert shoot_scale(count - 1, count, 200, tiny) == tiny
    for i in range(count):
        assert shoot_scale(i, count, 300, tiny) == 1.0
        assert shoot_scale(i, count, 316, tiny) == 1.0
        assert leaf_scale(i, 0, count, 300, tiny) == 1.0
        assert leaf_open(i, 0, count, 300) == 1.0
        assert root_scale(i, nseg, 300, tiny) == 1.0
        assert root_window(i, nseg)[0] >= node_arrived(i, nseg, 40, stub_first=True)
        assert root_window(i, nseg)[0] >= 40 or i == 0
    assert leaf_open(0, 1, count, 1) == 0.0
    assert tuck(0, count, 1) == 0.0
    assert tuck(count - 1, count, 1) == 1.0
    assert tuck(count - 1, count, 300) == 0.0
    for frame in (1, 40, 120, 200, 300, 316):
        for i in range(nseg):
            sy = rhizome_scale(i, nseg, frame, tiny)
            assert tiny - 1e-6 <= sy <= 1.0 + 1e-6
        for i in range(count):
            sy = shoot_scale(i, count, frame, tiny)
            assert tiny - 1e-6 <= sy <= 1.0 + 1e-6
    return "timeline ok"
