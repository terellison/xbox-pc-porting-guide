"""Generates a working folder + checklist for a single porting project."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from .xbe import XbeInfo

CHECKLIST_TEMPLATE = """# Porting checklist — {title}

Generated {timestamp} by `xboxport scaffold`.

## 0. Legal
- [ ] I own a legitimate copy of this game (disc or digital).
- [ ] This work is for personal/educational/preservation use, not distribution.
- [ ] I checked for an existing source port, decompilation project, or
      open-source reimplementation before starting from scratch.

## 1. Disc
- [ ] Disc imaged to `.iso` (or sourced from a personal backup).
- [ ] `xboxport iso-list <image.iso>` reviewed — note any unfamiliar
      top-level folders/extensions before extracting.
- [ ] `xboxport iso-extract <image.iso> ./extracted` run.

## 2. Executable
- [ ] `xboxport xbe-info ./extracted/default.xbe` run; title/region/sections
      below filled in from its output.
- [ ] Confirm which middleware/engine is in use (look at section names,
      string references in `.rdata`, and any bundled SDK readmes on disc).

## 3. Approach
Pick one (see ../xbox-porting-guide.md Step 4):
- [ ] Engine-based: known engine, source available, port assets onto it.
- [ ] Emulator/wrapper-based: run under xemu/Cxbx-Reloaded, shim Win32.
- [ ] Full decompile: disassemble in Ghidra/IDA, clean-room reimplement.

## 4. Build & test
- [ ] Toolchain chosen and a "hello world" stage builds for Windows.
- [ ] First milestone defined (e.g. "menu screen renders").

## Notes
- Title: {title}
- Title ID: {title_id}
- Disk #: {disk_number}
- Sections: {section_count}
"""

LAYOUT_DIRS = ("extracted", "analysis", "src", "notes")


def create_scaffold(output_dir: str, xbe_info: XbeInfo | None = None) -> str:
    for d in LAYOUT_DIRS:
        os.makedirs(os.path.join(output_dir, d), exist_ok=True)

    title = xbe_info.certificate.title_name if (xbe_info and xbe_info.certificate) else "(unknown)"
    title_id = f"0x{xbe_info.certificate.title_id:08X}" if (xbe_info and xbe_info.certificate) else "n/a"
    disk_number = xbe_info.certificate.disk_number if (xbe_info and xbe_info.certificate) else "n/a"
    section_count = len(xbe_info.sections) if xbe_info else "n/a"

    checklist_path = os.path.join(output_dir, "CHECKLIST.md")
    with open(checklist_path, "w") as f:
        f.write(
            CHECKLIST_TEMPLATE.format(
                title=title,
                title_id=title_id,
                disk_number=disk_number,
                section_count=section_count,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            )
        )
    return checklist_path
