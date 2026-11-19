#!/usr/bin/env python3
"""main.py — news-image-20261119 entrypoint (stdlib only).

Validates the bundled entry.png (PNG signature, <=1 MiB, 1024x1024) and
copies it to /output/entry.png. Deterministic: the same bytes every run.
"""
import os
import shutil
import struct
import sys

MAX_BYTES = 1048576
MAX_DIM = 1024


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        out_dir = "/output" if os.path.isdir("/output") else "out"
    out = os.path.join(out_dir, "entry.png")

    with open(src, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        print("entry.png: bad PNG signature", file=sys.stderr)
        return 1
    if len(data) > MAX_BYTES:
        print(f"entry.png: {len(data)} bytes > {MAX_BYTES}", file=sys.stderr)
        return 1
    # IHDR: width/height are big-endian uint32 at bytes 16..24.
    width, height = struct.unpack(">II", data[16:24])
    if width > MAX_DIM or height > MAX_DIM:
        print(f"entry.png: {width}x{height} > {MAX_DIM}x{MAX_DIM}",
              file=sys.stderr)
        return 1
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, out)
    print(f"wrote {out} ({len(data)} bytes, {width}x{height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
