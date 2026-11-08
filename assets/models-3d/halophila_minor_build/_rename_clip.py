"""Rename the baked glTF clip to Grow. Keeps the one animation and no camera."""

import json
import struct

PATHS = (
    r"d:\pepot\marinesee\app\assets\models-3d\halophila_minor.glb",
    r"d:\pepot\marinesee\assets\models-3d\halophila_minor\models\halophila_minor.glb",
)


def retitle(path):
    data = open(path, "rb").read()
    if data[:4] != b"glTF":
        raise SystemExit("not a glb: " + path)
    off = 12
    json_len, json_type = struct.unpack_from("<II", data, off)
    off += 8
    if json_type != 0x4E4F534A:
        raise SystemExit("missing json chunk")
    payload = json.loads(data[off : off + json_len])
    off += json_len
    bin_len, bin_type = struct.unpack_from("<II", data, off)
    off += 8
    binary = data[off : off + bin_len]
    names = []
    for anim in payload.get("animations", []):
        anim["name"] = "Grow"
        names.append(anim["name"])
    if payload.get("cameras"):
        raise SystemExit("camera leaked into " + path)
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    raw += b" " * ((4 - (len(raw) % 4)) % 4)
    total = 12 + 8 + len(raw) + 8 + len(binary)
    out = bytearray()
    out += b"glTF"
    out += struct.pack("<II", 2, total)
    out += struct.pack("<I", len(raw))
    out += b"JSON"
    out += raw
    out += struct.pack("<I", len(binary))
    out += b"BIN\x00"
    out += binary
    with open(path, "wb") as handle:
        handle.write(out)
    print(path, names, "cameras", payload.get("cameras"))


if __name__ == "__main__":
    for item in PATHS:
        retitle(item)
