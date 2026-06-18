#!/usr/bin/env python3
"""Build the Mario Kart 64 multiplayer hack ROM (Windows / Linux / macOS).

Two steps, matching the original Windows asm.cmd:
  1. assemble mk64_multiplayer_hack.asm with bass v14
  2. recalculate the N64 checksum via ../Tools/n64crc.py

The bass binary MUST be v14 with the one-line `dd`-width patch (see
BUILD_NOTES.md); an unpatched bass produces a ROM that white-screens after
the logo.

Usage:
  python build.py [-o OUTPUT] [--bass PATH] [--sym FILE]

bass is located in this order: --bass arg, then $BASS, then `bass`/`bass.exe`
on PATH.
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.normpath(os.path.join(HERE, "..", "LIB"))
TOOLS = os.path.normpath(os.path.join(HERE, "..", "Tools"))
ASM = "mk64_multiplayer_hack.asm"
CLEAN_ROM = os.path.join(LIB, "Mario Kart 64 (U) [!].z64")


def find_bass(explicit):
    for c in (explicit, os.environ.get("BASS")):
        if c:
            if os.path.isfile(c):
                return c
            sys.exit(f"error: bass not found at: {c}")
    found = shutil.which("bass") or shutil.which("bass.exe")
    if found:
        return found
    sys.exit(
        "error: bass not found. Pass --bass PATH, set $BASS, or put it on PATH.\n"
        "Build bass v14 with the dd=4 patch first (see BUILD_NOTES.md)."
    )


def main():
    ap = argparse.ArgumentParser(description="Build the MK64 multiplayer hack ROM.")
    ap.add_argument("-o", "--output", default="mk64_multiplayer_hack.z64",
                    help="output ROM path (default: %(default)s)")
    ap.add_argument("--bass", help="path to the patched bass v14 binary")
    ap.add_argument("--sym", help="optional path to write a bass symbol file")
    args = ap.parse_args()

    # Run from the asm's directory so its "../LIB/..." includes resolve
    # regardless of where build.py was invoked from.
    os.chdir(HERE)

    if not os.path.isfile(CLEAN_ROM):
        sys.exit(
            f"error: clean ROM not found at {CLEAN_ROM}\n"
            "Place the US (U)[!] ROM there (md5 3a67d9986f54eb282924fca4cd5f6dff)."
        )

    bass = find_bass(args.bass)

    cmd = [bass, "-o", args.output]
    if args.sym:
        cmd += ["-sym", args.sym]
    cmd.append(ASM)
    print("[1/2] assembling:", " ".join(cmd))
    if subprocess.run(cmd).returncode != 0:
        sys.exit("error: bass assembly failed")

    crc = os.path.join(TOOLS, "n64crc.py")
    print("[2/2] fixing checksum:", crc)
    if subprocess.run([sys.executable, crc, CLEAN_ROM, args.output]).returncode != 0:
        sys.exit("error: checksum fix failed")

    print(f"done: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
