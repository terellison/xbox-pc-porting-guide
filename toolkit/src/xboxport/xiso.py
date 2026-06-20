"""Reader/extractor for the XDVDFS filesystem used on Xbox discs and XISO images.

XDVDFS is a documented, ISO9660-adjacent filesystem format (see
xboxdevwiki.net/XDVDFS) — reading it is no different in kind from reading
ISO9660 or FAT. This module only walks the directory tree and copies file
bytes; it never inspects or interprets the game data itself.
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass

SECTOR_SIZE = 2048
MAGIC = b"MICROSOFT*XBOX*MEDIA"
VOLUME_DESCRIPTOR_SECTOR = 32
ATTR_DIRECTORY = 0x10

_DIRENT_STRUCT = struct.Struct("<HHIIBB")  # left, right, sector, size, attrs, name_len


class XisoError(ValueError):
    pass


@dataclass
class XisoEntry:
    path: str
    is_directory: bool
    sector: int
    size: int


def _read_volume_descriptor(f) -> tuple[int, int]:
    f.seek(VOLUME_DESCRIPTOR_SECTOR * SECTOR_SIZE)
    data = f.read(SECTOR_SIZE)
    if len(data) < SECTOR_SIZE or data[0:20] != MAGIC or data[0x7EC : 0x7EC + 20] != MAGIC:
        raise XisoError("Not a valid XISO image (volume descriptor magic mismatch)")
    root_sector, root_size = struct.unpack_from("<II", data, 0x14)
    return root_sector, root_size


def _parse_directory_table(data: bytes) -> list[tuple[str, int, int, int]]:
    """In-order walk of the binary search tree stored in one directory's table."""
    entries: list[tuple[str, int, int, int]] = []
    visited: set[int] = set()

    def visit(word_offset: int) -> None:
        # Callers only ever pass 0 for the table's root entry; child calls are
        # guarded by `if left:` / `if right:` below, since 0 there means "no child".
        byte_off = word_offset * 4
        if byte_off in visited or byte_off + _DIRENT_STRUCT.size > len(data):
            return
        visited.add(byte_off)
        if data[byte_off : byte_off + 14] == b"\xff" * 14:
            return  # unused padding
        left, right, sector, size, attrs, name_len = _DIRENT_STRUCT.unpack_from(data, byte_off)
        name_start = byte_off + _DIRENT_STRUCT.size
        name = data[name_start : name_start + name_len].decode("ascii", errors="replace")
        if left:
            visit(left)
        entries.append((name, sector, size, attrs))
        if right:
            visit(right)

    visit(0)
    return entries


def _walk(f, sector: int, size: int, prefix: str, out: list[XisoEntry]) -> None:
    f.seek(sector * SECTOR_SIZE)
    data = f.read(size)
    for name, esector, esize, attrs in _parse_directory_table(data):
        is_dir = bool(attrs & ATTR_DIRECTORY)
        entry_path = f"{prefix}/{name}" if prefix else name
        out.append(XisoEntry(path=entry_path, is_directory=is_dir, sector=esector, size=esize))
        if is_dir and esize > 0:
            _walk(f, esector, esize, entry_path, out)


def list_iso(path: str) -> list[XisoEntry]:
    with open(path, "rb") as f:
        root_sector, root_size = _read_volume_descriptor(f)
        entries: list[XisoEntry] = []
        _walk(f, root_sector, root_size, "", entries)
        return entries


def extract_iso(path: str, out_dir: str) -> list[str]:
    """Extract every file in the image under out_dir, preserving its directory structure."""
    extracted: list[str] = []
    with open(path, "rb") as f:
        root_sector, root_size = _read_volume_descriptor(f)
        entries: list[XisoEntry] = []
        _walk(f, root_sector, root_size, "", entries)
        for entry in entries:
            dest = os.path.join(out_dir, *entry.path.split("/"))
            if entry.is_directory:
                os.makedirs(dest, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            f.seek(entry.sector * SECTOR_SIZE)
            with open(dest, "wb") as out_f:
                remaining = entry.size
                while remaining > 0:
                    chunk = f.read(min(1 << 20, remaining))
                    if not chunk:
                        break
                    out_f.write(chunk)
                    remaining -= len(chunk)
            extracted.append(entry.path)
    return extracted
