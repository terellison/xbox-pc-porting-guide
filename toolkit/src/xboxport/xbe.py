"""Parser for the Xbox Executable (.xbe) container format.

Field layout follows the publicly documented XBE_IMAGE_HEADER /
XBE_CERTIFICATE / XBE_SECTIONHEADER structures (see xboxdevwiki.net/Xbe
and xboxdevwiki.net/Certificate). This only reads container metadata —
header fields, section table, certificate — never the code/data payload
semantics inside the sections.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

MAGIC = b"XBEH"

# Entry points and kernel import thunks are XOR-obfuscated with one of a
# small, publicly known set of keys depending on which kernel built the XBE.
ENTRY_POINT_KEYS = {
    "retail": 0xA8FC57AB,
    "debug": 0x94859D4B,
    "beta": 0xE682F45B,
}
KERNEL_THUNK_KEYS = {
    "retail": 0x5B6D40B6,
    "debug": 0xEFB1F152,
    "beta": 0x46437DCD,
}

_HEADER_OFFSET = 0x104
_HEADER_FIELDS = [
    "base",
    "size_of_headers",
    "size_of_image",
    "size_of_image_header",
    "time_date",
    "certificate_addr",
    "number_of_sections",
    "section_headers_addr",
    "init_flags",
    "entry_addr_raw",
    "tls_addr",
    "pe_stack_commit",
    "pe_heap_reserve",
    "pe_heap_commit",
    "pe_base_addr",
    "pe_size_of_image",
    "pe_checksum",
    "pe_time_date",
    "debug_pathname_addr",
    "debug_filename_addr",
    "debug_unicode_filename_addr",
    "kernel_image_thunk_addr_raw",
    "non_kernel_import_dir_addr",
    "library_versions_count",
    "library_versions_addr",
    "kernel_library_version_addr",
    "xapi_library_version_addr",
    "logo_bitmap_addr",
    "logo_bitmap_size",
]
_HEADER_STRUCT = struct.Struct("<" + "I" * len(_HEADER_FIELDS))

_CERT_STRUCT = struct.Struct("<3I 80s 16I 5I")
_SECTION_STRUCT = struct.Struct("<9I 20s")


class XbeError(ValueError):
    pass


@dataclass
class XbeCertificate:
    title_id: int
    title_name: str
    allowed_media: int
    game_region: int
    game_ratings: int
    disk_number: int
    version: int


@dataclass
class XbeSection:
    name: str
    flags: int
    virtual_addr: int
    virtual_size: int
    file_addr: int
    file_size: int


@dataclass
class XbeInfo:
    base: int
    size_of_image: int
    entry_addr: int
    entry_kernel: str
    kernel_image_thunk_addr: int
    kernel_thunk_kernel: str
    certificate: XbeCertificate | None
    sections: list[XbeSection] = field(default_factory=list)


def _resolve_xor(raw: int, keys: dict, base: int, size_of_image: int) -> tuple[int, str]:
    for name, key in keys.items():
        candidate = raw ^ key
        if base <= candidate <= base + size_of_image:
            return candidate, name
    return raw, "unknown"


def _read_cstring(data: bytes, offset: int) -> str:
    end = data.find(b"\x00", offset)
    if end == -1:
        end = len(data)
    return data[offset:end].decode("ascii", errors="replace")


def parse_xbe(path: str) -> XbeInfo:
    with open(path, "rb") as f:
        data = f.read()

    if data[:4] != MAGIC:
        raise XbeError(f"Not an XBE file (bad magic): {path!r}")
    if len(data) < _HEADER_OFFSET + _HEADER_STRUCT.size:
        raise XbeError(f"File too short to contain an XBE header: {path!r}")

    values = _HEADER_STRUCT.unpack_from(data, _HEADER_OFFSET)
    h = dict(zip(_HEADER_FIELDS, values))

    def v2f(virtual_addr: int) -> int:
        """Resolve a virtual address inside the header region to a file offset."""
        return virtual_addr - h["base"]

    entry_addr, entry_kernel = _resolve_xor(
        h["entry_addr_raw"], ENTRY_POINT_KEYS, h["base"], h["size_of_image"]
    )
    thunk_addr, thunk_kernel = _resolve_xor(
        h["kernel_image_thunk_addr_raw"], KERNEL_THUNK_KEYS, h["base"], h["size_of_image"]
    )

    certificate = None
    cert_off = v2f(h["certificate_addr"])
    if h["certificate_addr"] and 0 <= cert_off <= len(data) - _CERT_STRUCT.size:
        (
            _size,
            _time_date,
            title_id,
            title_name_raw,
            *alt_ids_and_rest,
        ) = _CERT_STRUCT.unpack_from(data, cert_off)
        allowed_media, game_region, game_ratings, disk_number, version = alt_ids_and_rest[-5:]
        title_name = title_name_raw.decode("utf-16-le", errors="replace").rstrip("\x00")
        certificate = XbeCertificate(
            title_id=title_id,
            title_name=title_name,
            allowed_media=allowed_media,
            game_region=game_region,
            game_ratings=game_ratings,
            disk_number=disk_number,
            version=version,
        )

    sections: list[XbeSection] = []
    sec_off = v2f(h["section_headers_addr"])
    for i in range(h["number_of_sections"]):
        offset = sec_off + i * _SECTION_STRUCT.size
        if offset < 0 or offset + _SECTION_STRUCT.size > len(data):
            break
        (
            flags,
            virtual_addr,
            virtual_size,
            file_addr,
            file_size,
            name_addr,
            _name_ref_count,
            _head_shared_ref_addr,
            _tail_shared_ref_addr,
            _digest,
        ) = _SECTION_STRUCT.unpack_from(data, offset)
        name_off = v2f(name_addr)
        name = _read_cstring(data, name_off) if 0 <= name_off < len(data) else "?"
        sections.append(
            XbeSection(
                name=name,
                flags=flags,
                virtual_addr=virtual_addr,
                virtual_size=virtual_size,
                file_addr=file_addr,
                file_size=file_size,
            )
        )

    return XbeInfo(
        base=h["base"],
        size_of_image=h["size_of_image"],
        entry_addr=entry_addr,
        entry_kernel=entry_kernel,
        kernel_image_thunk_addr=thunk_addr,
        kernel_thunk_kernel=thunk_kernel,
        certificate=certificate,
        sections=sections,
    )


def format_report(info: XbeInfo) -> str:
    lines = []
    if info.certificate:
        c = info.certificate
        lines.append(f"Title:       {c.title_name!r}")
        lines.append(f"Title ID:    0x{c.title_id:08X}")
        lines.append(f"Disk:        {c.disk_number}")
        lines.append(f"Version:     {c.version}")
        lines.append(f"Region mask: 0x{c.game_region:08X}")
    else:
        lines.append("Title:       (no certificate found)")
    lines.append(f"Base addr:   0x{info.base:08X}")
    lines.append(f"Image size:  0x{info.size_of_image:08X}")
    lines.append(f"Entry point: 0x{info.entry_addr:08X}  ({info.entry_kernel} kernel)")
    lines.append(
        f"Kernel thunk:0x{info.kernel_image_thunk_addr:08X}  ({info.kernel_thunk_kernel} kernel)"
    )
    lines.append(f"Sections ({len(info.sections)}):")
    for s in info.sections:
        lines.append(
            f"  {s.name:<16} vaddr=0x{s.virtual_addr:08X} vsize=0x{s.virtual_size:06X} "
            f"file_off=0x{s.file_addr:08X} file_size=0x{s.file_size:06X}"
        )
    return "\n".join(lines)
