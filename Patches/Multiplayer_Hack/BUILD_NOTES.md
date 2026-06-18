# Build Notes (Linux)

How to build this patch, reconstructed since the original repo's instructions
(a Windows `asm.cmd` + a Google Drive download) are unavailable.

## What this "patch" actually is

It is **not** a binary patch (no `.ips` / `.bps`). It is **assembly source**
for the [`bass`](https://github.com/ARM9/bass) assembler (byuu's assembler,
ARM9's N64 fork). You "apply" it by **assembling it against a clean ROM** —
bass embeds the original ROM via `insert` and overwrites specific regions.

## Verified working procedure

1. **Assembler: bass v14** (NOT v18 — see note below).

   ```
   git clone --depth 1 --branch v14 https://github.com/ARM9/bass.git
   cd bass/bass && make          # binary is ./bass
   ```

2. **Clean ROM** at `Patches/LIB/Mario Kart 64 (U) [!].z64`
   md5 `3a67d9986f54eb282924fca4cd5f6dff` (US `(U) [!]`). Already in place.

3. **Build**, from `Patches/Multiplayer_Hack/`:

   ```
   /path/to/bass -o mk64_hack.z64 mk64_multiplayer_hack.asm
   ```

   Produces a 12 MB (`0xC00000`) Z64 with header `80 37 12 40`.

On this machine bass v14 is built at `/home/brian/code/bass-v14/bass/bass`.

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
