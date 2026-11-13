"""One low sand mound. The size is a display choice so the shoots sit in it."""

import math

import bmesh

from pinifolia_next.meshutil import finish_mesh


# Display choice: one low oval. The shoots sit inside it, and the roots stay in it.
_CX, _CY = 0.03, 0.01
_RX, _RY = 0.42, 0.32


def _radius(x, y):
    nx = (x - _CX) / _RX
    ny = (y - _CY) / _RY
    return math.sqrt(nx * nx + ny * ny)


def sand_height(x, y):
    r = _radius(x, y)
    if r >= 1.0:
        return -0.016
    dome = 0.028 * (1.0 - r ** 1.7)
    # Gentle ripples only. A tight wave reads as a grid.
    ripple = 0.0008 * math.sin(x * 14.0 + y * 6.0) * math.cos(y * 11.0) * (1.0 - r)
    return -0.016 + dome + ripple


def sand_object(material, collection):
    bm = bmesh.new()
    nx, ny = 68, 52  # display resolution
    x0, x1 = _CX - _RX, _CX + _RX
    y0, y1 = _CY - _RY, _CY + _RY
    grid = []
    radii = []
    for j in range(ny):
        row = []
        rad = []
        v = -1.0 + 2.0 * j / (ny - 1)
        for i in range(nx):
            u = -1.0 + 2.0 * i / (nx - 1)
            r = math.sqrt(u * u + v * v)
            if r > 1.0:
                u /= r
                v_use = v / r
                r = 1.0
            else:
                v_use = v
            x = _CX + u * _RX
            y = _CY + v_use * _RY
            row.append(bm.verts.new((x, y, sand_height(x, y))))
            rad.append(r)
        grid.append(row)
        radii.append(rad)
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for j in range(ny - 1):
        for i in range(nx - 1):
            if min(radii[j][i], radii[j][i + 1], radii[j + 1][i], radii[j + 1][i + 1]) > 0.995:
                continue
            face = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop in face.loops:
                p = loop.vert.co
                loop[uv_layer].uv = ((p.x - x0) / (x1 - x0), (p.y - y0) / (y1 - y0))
    obj = finish_mesh(bm, "Sand", material, collection, normals="up")
    return obj
