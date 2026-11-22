#!/usr/bin/env python3
"""Copy the pre-rendered front page to the grader output directory.

The image is drawn at build time by render.py and committed as entry.png;
this program only copies it (stdlib only, no network, deterministic).
"""
import hashlib
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "entry.png"


def main() -> int:
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "out"))
    out_dir.mkdir(parents=True, exist_ok=True)
    data = SRC.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        print("entry.png is not a PNG file", file=sys.stderr)
        return 1
    digest = hashlib.sha256(data).hexdigest()
    dest = out_dir / "entry.png"
    shutil.copyfile(SRC, dest)
    check = hashlib.sha256(dest.read_bytes()).hexdigest()
    if check != digest:
        print(f"sha256 mismatch: {check} != {digest}", file=sys.stderr)
        return 1
    if len(data) > 1048576:
        print(f"entry.png over 1 MiB: {len(data)} bytes", file=sys.stderr)
        return 1
    print(f"entry.png copied: {len(data)} bytes sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
