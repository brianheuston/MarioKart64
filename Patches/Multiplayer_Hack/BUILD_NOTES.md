# Build Notes (Linux)

How to build this patch, reconstructed since the original repo's instructions
(a Windows `asm.cmd` + a Google Drive download) are unavailable.

## What this "patch" actually is

It is **not** a binary patch (no `.ips` / `.bps`). It is **assembly source**
for the [`bass`](https://github.com/ARM9/bass) assembler (byuu's assembler,
ARM9's N64 fork). You "apply" it by **assembling it against a clean ROM** —
bass embeds the original ROM via `insert` and overwrites specific regions.

## Quick build

Once a patched bass v14 exists (step 1 below), `build.py` runs the assemble +
checksum steps in one go, on Windows or Linux:

```
python build.py --bass /path/to/bass        # or set $BASS / put bass on PATH
```

## Verified working procedure

1. **Assembler: bass v14, with a one-line patch** (NOT v18 — see notes below).

   ```
   git clone --depth 1 --branch v14 https://github.com/ARM9/bass.git
   cd bass/bass
   # REQUIRED patch: make the `dd` directive emit 4 bytes, not 8 (see note).
   # In core/core.hpp, the EmitBytes table: change `{"dq ", 8}` to `{"dq ", 4}`.
   sed -i 's/{"dq ", 8}/{"dq ", 4}/' core/core.hpp
   make                          # binary is ./bass
   ```

2. **Clean ROM** at `Patches/LIB/Mario Kart 64 (U) [!].z64`
   md5 `3a67d9986f54eb282924fca4cd5f6dff` (US `(U) [!]`). Already in place.

3. **Build**, from `Patches/Multiplayer_Hack/`:

   ```
   /path/to/bass -o mk64_hack.z64 mk64_multiplayer_hack.asm
   ```

   Produces a 12 MB (`0xC00000`) Z64 with header `80 37 12 40`.

4. **Fix the N64 checksum** (REQUIRED — see note below):

   ```
   python3 ../Tools/n64crc.py "../LIB/Mario Kart 64 (U) [!].z64" mk64_hack.z64
   ```

On this machine bass v14 is built (with the patch) at
`/home/brian/code/bass-v14/bass/bass`.

## IMPORTANT: the `dd` directive must emit 4 bytes

The source uses `dd` ~131 times for 32-bit values — menu-table counts and
pointers (`dd 0x00000002`, `dd MenuEntry1`, ...) and character stats — and the
code reads them with a 4-byte stride (`lw t2, 0x04(t0)`). The author's
assembler treated `dd` as a 4-byte word.

bass v14's mipseb arch table (`arch/table/mipseb/directives.md`) maps `dd` to
the 8-byte emit slot, so an unpatched v14 builds every menu pointer as
`00 00 00 00 xx xx xx xx`. A 32-bit read then returns `0` (a null) for every
count and pointer — the title menu dereferences garbage and hangs on a white
screen *after* the Nintendo logo (the boot/logo still work; input still
responds). The `core.hpp` patch above changes that slot to 4 bytes, which is
also bass's own core default. (We can't just remap `dd` to the existing 4-byte
slot in the arch table — that slot belongs to `dw`, and aliasing them breaks
`dw`.) Verify after building: the `MenuStrings` table should read
`00 00 00 02  80 00 .. ..  ...` with a 4-byte stride.

## IMPORTANT: the checksum MUST be recalculated after building

The patch overwrites code inside the boot-checked region (`0x1000`–`0x101000`;
e.g. the asm's `origin 0x001E6C` / `0x0029F0`). That invalidates the ROM's
header CRC (bytes `0x10`–`0x17`). On boot the IPL3/CIC checksum handshake then
fails and the bootcode spins forever — Project64 reports *"in a permanent loop
that cannot be exited."* The original Windows `asm.cmd` ran a CRC fixer after
bass; we replicate that with `Patches/Tools/n64crc.py` (CIC-6102 algorithm,
self-validated against the clean ROM's known-good CRC before writing).

## IMPORTANT: use bass v14, not v18

bass **v18 will not build this project.** v18 changed the `constant` directive
syntax from `constant name(value)` (used throughout `N64.INC`,
`functions.inc`, and the main asm) to `constant name = value`. Under v18 the
old form misparses and fails with `constant cannot be modified`. v14 is the
last release that uses the `name(value)` form and the `scope`/`{param}` macro
dialect this project relies on.

(bass v18 was also tried and installed at `~/.local/bin/bass` during
investigation — leave it alone or remove it; it is not used for this build.)

## Fixes applied to make it build on Linux

- **Include paths:** converted Windows `..\LIB\...` backslashes to `../LIB/...`
  in `mk64_multiplayer_hack.asm` (lines 5–7, 10).
- **Filename case:** the include said `N64.inc` but the file is `N64.INC`;
  corrected to `N64.INC` (Linux is case-sensitive; Windows didn't care).
- **Stray space:** `functions.inc:45` had `constant PrintText2 (...)`; the space
  made v14 read the name as `"PrintText2 "` and warn. Removed the space to
  match the sibling lines. (That symbol is unused — `PrintText2Cord` is the one
  actually referenced — so it was harmless, but the build is now warning-free.)

## The "locked" Windows instructions, decoded

The README's `asm.cmd` + Google Drive download was just a Windows wrapper
bundling `bass.exe`. There are no missing source or asset files: the only
external references in the `.asm` are the three `LIB/*.inc` includes,
`stats_yoshi.asm`, and the ROM `insert`. The runtime DMA at `0xBE9170` +
`0x16E90` = `0xC00000` is the tail of the stock ROM, not an external asset.
