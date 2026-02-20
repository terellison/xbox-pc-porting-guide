# Xbox Game to PC Porting Guide

## Overview
Decompile an original Xbox (1st gen) game disc and recompile for Windows.

---

## Legal Disclaimer
⚠️ **Important:**
- Decompiling code from proprietary software may violate copyright laws (DMCA, EULAs)
- Some games have open-source reimplementations (e.g., OpenXDK alternatives)
- Only do this for games you own and for personal/educational use
- Check if a clean-room reimplementation or source port already exists first

---

## Step 1: Dump the Disc

### Required Tools
- Xbox DVD drive (or external USB enclosure)
- `xiso` or `imgburn` — extract disc image (.iso)
- Xbox Insider Toolkit or `extract-xiso`

```bash
# Install extraction tool
brew install xiso  # or download from GitHub

# Extract disc
xiso -x game.iso ./output_folder
```

---

## Step 2: Analyze the Executable

### Xbox Executable Format (.xbe)
- Xbox uses `.xbe` (Xbox Executable) format, not PE (.exe)
- Contains signature, certificate, headers, sections

### Tools
- **xbedump** — inspect .xbe headers
- **xbetool** — extract sections, resources
- **Cxbx-Reloaded** — Xbox emulator with debug info (can extract code)

```bash
# Inspect .xbe
xbedump game.xbe

# Extract all sections
xbetool extract game.xbe ./extracted/
```

---

## Step 3: Understand the Code

### Xbox Architecture
- **CPU:** Intel Pentium III (x86)
- **GPU:** NVIDIA NV2A (custom GeForce 3)
- **OS:** Custom Xbox kernel (like Win2000内核)

### Key Challenges
1. **Direct hardware access** — Xbox kernel calls, not Win32 API
2. **Graphics API** — Xbox uses custom D3D8 wrappers, not D3D9/11
3. **Audio** — Xbox Sound System (XAudio predecessor)
4. **No filesystem** — cached disc reads, not file I/O

### What You'll Find
- Compiled C/C++ (likely MSVC v6 or 2003)
- Inline assembly for performance
- Custom middleware (Unreal Engine 2, RenderWare)

---

## Step 4: Port to Windows

### Approach A: Emulator-Based (Easier)
Use **Cxbx-Reloaded** or **xqemu** and build a wrapper:
1. Add Win32 API shims
2. Replace Xbox kernel calls with Win32 equivalents
3. Map D3D8 → D3D9 or D3D11

### Approach B: Full Decompile (Hard)
1. Disassemble code with **IDA Pro** or **Ghidra**
2. Reconstruct C code (clean-room, don't copy-paste)
3. Replace Xbox APIs with Win32
4. Recompile with MSVC or MinGW

### Approach C: Open-Source Engine (Best)
If the game uses a known engine (Unreal 2, RenderWare):
1. Find the engine source
2. Extract game assets (models, textures, scripts)
3. Build against Windows-compatible engine

---

## Step 5: Build & Test

```bash
# If using MSVC
cl /O2 /GL game_code.cpp /link /SUBSYSTEM:CONSOLE

# Or MinGW
g++ -O2 game_code.cpp -o game.exe -lws2_32 -ld3d9
```

### Testing
- Run in Windows compatibility mode if needed
- Debug with WinDbg or Visual Studio
- Expect graphics/audio glitches

---

## Existing Projects to Reference

| Project | Description |
|---------|-------------|
| [OpenXDK](https://github.com/OpenXDK/OpenXDK) | Open-source Xbox dev kit |
| [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded) | Xbox emulator (good for reference) |
| [Dxbx](https://github.com/DxbxPC2XB_DLL) | DirectX wrapper |
| [OpenMW](https://openmw.org/) | Morrowind reimplementation (engine-based port example) |

---

## Recommended Workflow

1. **Verify** no existing PC port or source port exists
2. **Extract** disc image and inspect .xbe
3. **Identify** engine/middleware used
4. **Choose approach:**
   - Engine-based port (cleanest)
   - Wrapper/emulator approach (easiest)
   - Full decompilation (most work, legal risk)
5. **Start small** — get a menu screen running first
6. **Join community** — Xbox hacking Discord, GBAtemp forums

---

## Quick Start Commands

```bash
# 1. Get xbedump
git clone https://github.com/mborgerson/xbedump.git
cd xbedump && mkdir build && cd build && cmake .. && make

# 2. Inspect your game
./xbedump /path/to/default.xbe

# 3. Extract resources
git clone https://github.com/bushwick-internet/xbetool.git
./xbetool -x default.xbe ./extracted/
```

---

*This guide is for educational purposes. Respect copyright.*
