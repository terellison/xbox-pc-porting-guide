# Xbox Game to PC Porting Guide

## Overview
Take a game you own on original Xbox (1st gen) disc and get it running on
Windows — either by running it under a compatibility layer/emulator, or by
fully decompiling and recompiling it for native Windows.

There's a companion CLI, [`xboxport`](toolkit/README.md), that automates the
mechanical, legal part of this (disc extraction + executable inspection) so
you can spend your time on the actual porting work. See
[`docs/ninja-gaiden-black-case-study.md`](docs/ninja-gaiden-black-case-study.md)
for a worked example of why this matters: Team Ninja has confirmed the
*Ninja Gaiden Black* source is lost, so any modern preservation effort has to
start exactly where this guide starts — at the disc.

---

## Legal Disclaimer
⚠️ **Important:**
- Decompiling proprietary software can implicate copyright law (and the
  DMCA's anti-circumvention provisions) even when you own the disc.
- Only do this for games you own, for personal/educational/preservation use.
  Don't distribute disc images, extracted assets, or decompiled source.
- Check whether a clean-room reimplementation, source port, or working
  emulator profile already exists before starting from scratch — see
  [Existing Projects to Reference](#existing-projects-to-reference).

---

## Step 1: Dump the Disc

### Required Tools
- An original Xbox (or a DVD drive that can read the disc's special layout)
- [`extract-xiso`](https://github.com/XboxDev/extract-xiso) — create/extract `.iso` images of Xbox discs
- `xboxport iso-list` / `xboxport iso-extract` (this repo's toolkit) — inspect and pull files out of an existing `.iso` without needing a drive at all

```bash
# Build extract-xiso from source (Linux/macOS/Windows via cmake)
git clone https://github.com/XboxDev/extract-xiso.git
cd extract-xiso && cmake -B build && cmake --build build

# List then extract
./build/extract-xiso -l game.iso
./build/extract-xiso -x game.iso

# Or, using this repo's toolkit on an existing image:
xboxport iso-list game.iso
xboxport iso-extract game.iso ./extracted
```

---

## Step 2: Analyze the Executable

### Xbox Executable Format (.xbe)
- Xbox uses `.xbe` (Xbox Executable), not PE (.exe) — a related but distinct
  container format with its own header, certificate, and section table.

### Tools
- [`xbedump`](https://github.com/XboxDev/xbedump) — dump/sign `.xbe` headers
- [`pyxbe`](https://github.com/mborgerson/pyxbe) — Python library to read/write `.xbe`
- `xboxport xbe-info` (this repo's toolkit) — prints title, entry point, certificate, and section table
- [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded) / [xemu](https://github.com/xemu-project/xemu) — emulators that already parse and load `.xbe`; useful as a working reference implementation

```bash
xboxport xbe-info ./extracted/default.xbe
```

---

## Step 3: Understand the Code

### Xbox Architecture
- **CPU:** Intel Pentium III–class (x86, no SSE2)
- **GPU:** NVIDIA NV2A (custom GeForce 3-derived part)
- **OS:** A heavily modified, stripped-down kernel derived from Windows 2000 — exposes Xbox-specific kernel calls, not the Win32 API

### Key Challenges
1. **Direct hardware/kernel access** — games call the Xbox kernel directly, not Win32
2. **Graphics API** — a custom D3D8-derived API talking straight to NV2A, not D3D9/11/12
3. **Audio** — the original Xbox Sound System (predates XAudio)
4. **Storage access** — reads come from the XDVDFS-formatted disc/cache rather than a general filesystem

### What You'll Find
- Compiled C/C++ (commonly built with an MSVC-derived toolchain from the early-2000s XDK)
- Inline assembly in hot paths
- Often a recognizable middleware/engine (Unreal Engine 2, RenderWare, or an in-house engine)

---

## Step 4: Port to Windows

### Approach A: Emulator/Compatibility Layer (Easiest)
Run the game under [xemu](https://xemu.app/) or [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded) first — check their compatibility lists, since many titles already run with no extra work:
1. If it's not yet supported, the emulator's HLE kernel/Win32 shim layer is the reference for what a wrapper needs to do.
2. Map D3D8 calls → D3D9/11/12 (both emulators already do this; read their source for the mapping).

### Approach B: Engine-Based Port (Best, if applicable)
If the game uses a known engine (Unreal Engine 2, RenderWare, etc.):
1. Find the matching open-source/PC engine version.
2. Extract assets (models, textures, audio, scripts) from the disc.
3. Rebuild the game's content pipeline against the Windows-compatible engine.

### Approach C: Full Decompile (Hardest, most legal risk)
1. Disassemble with [Ghidra](https://github.com/NationalSecurityAgency/ghidra) or IDA Pro.
2. Reconstruct readable C/C++ — **clean-room**: write your own implementation
   from the disassembly's observed behavior, don't transcribe verbatim.
3. Replace Xbox kernel/D3D8 calls with Win32/D3D equivalents.
4. Recompile with MSVC or MinGW.

For homebrew/from-scratch Xbox-side development (not strictly needed for a
PC port, but useful for understanding the XDK conventions a game was built
against), the actively maintained SDK is
[nxdk](https://github.com/XboxDev/nxdk) — it supersedes the now-inactive
OpenXDK.

---

## Step 5: Build & Test

```bash
# MSVC
cl /O2 /GL game_code.cpp /link /SUBSYSTEM:WINDOWS d3d9.lib

# MinGW
g++ -O2 game_code.cpp -o game.exe -ld3d9
```

### Testing
- Diff behavior against the original running in xemu/Cxbx-Reloaded — it's
  your reference implementation for "what correct looks like."
- Debug with WinDbg or Visual Studio.
- Expect graphics/audio mismatches first; gameplay logic and assets are
  usually easier than the renderer.

---

## Existing Projects to Reference

| Project | Description |
|---------|-------------|
| [extract-xiso](https://github.com/XboxDev/extract-xiso) | Create/extract Xbox disc images |
| [xbedump](https://github.com/XboxDev/xbedump) | Dump/sign `.xbe` headers |
| [pyxbe](https://github.com/mborgerson/pyxbe) | Python `.xbe` reader/writer |
| [nxdk](https://github.com/XboxDev/nxdk) | Modern, maintained open-source Xbox SDK (successor to OpenXDK) |
| [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded) | Xbox-to-Windows HLE emulator/compatibility layer |
| [xemu](https://github.com/xemu-project/xemu) | Actively maintained original Xbox emulator (successor to xqemu) |
| [Dxbx](https://github.com/PatrickvL/Dxbx) | Delphi-based Xbox1 HLE emulator |
| [DECOMP__Ninja](https://github.com/mehmetalinya/DECOMP__Ninja) | Community decompilation attempt for Ninja Gaiden Black/2 — see the [case study](docs/ninja-gaiden-black-case-study.md) |

---

## Recommended Workflow

1. **Verify** no existing PC port, source port, or playable emulator profile exists.
2. **Extract** the disc image (`xboxport iso-extract`) and inspect `default.xbe` (`xboxport xbe-info`).
3. **Identify** the engine/middleware in use.
4. **Choose an approach** — engine-based (cleanest), emulator/wrapper (easiest), or full decompile (most work, most legal risk).
5. **Start small** — get a menu screen rendering before tackling gameplay.
6. **Scaffold the project**: `xboxport scaffold ./my-port --xbe ./extracted/default.xbe` generates a checklist and working folders.
7. **Join the community** — Cxbx-Reloaded/xemu Discords, GBAtemp, XboxDev — someone has often already solved your exact problem.

---

*This guide is for personal/educational/preservation use on games you own. Respect copyright.*
