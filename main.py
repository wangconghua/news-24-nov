#!/usr/bin/env python3
"""Entry point: render the front page and place it where the harness reads it.

Writes entry.png next to this file, then copies it to /output/entry.png.
Fully deterministic: running twice yields byte-identical output.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import render


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    local_png = os.path.join(here, "entry.png")
    notes = render.build(local_png)
    if notes:
        print("layout notes:", notes)
    out_dir = "/output"
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(local_png, os.path.join(out_dir, "entry.png"))
    print("wrote entry.png and /output/entry.png")


if __name__ == "__main__":
    main()
