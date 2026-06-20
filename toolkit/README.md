# xboxport

A small CLI for the legal, mechanical front-end of porting an original
Xbox game *you own* to PC: reading the disc filesystem and inspecting the
executable container. It does not decompile, disassemble, or reproduce any
proprietary game code — see [Scope](#scope) below.

## Install

```bash
cd toolkit
pip install -e .
```

## Usage

```bash
# List everything on a disc image (sectors are read directly, no extraction)
xboxport iso-list game.iso

# Extract every file from the image to a folder
xboxport iso-extract game.iso ./extracted

# Inspect the executable: title, entry point, sections, certificate
xboxport xbe-info ./extracted/default.xbe

# Generate a working folder + checklist for the rest of the port
xboxport scaffold ./my-port --xbe ./extracted/default.xbe
```

## Scope

| Format | What's read | Why it's fine to parse |
|---|---|---|
| XDVDFS (XISO) | Directory tree + raw file bytes | Documented disc filesystem format, same category as reading ISO9660/FAT |
| XBE header/certificate/sections | Container metadata (title, entry point, section table) | Documented executable container format — like reading PE/ELF headers |

`xboxport` never disassembles `.text`, never inspects game logic, and never
ships or downloads anyone's copyrighted assets. The actual decompilation
step (Ghidra/IDA, clean-room reimplementation) is deliberately left to the
human, per the legal disclaimer in [`../xbox-porting-guide.md`](../xbox-porting-guide.md).

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests run against synthetic XBE/XISO byte structures built in-memory —
no real game data is included in this repo.
