"""Tests against a synthetic .xbe built in-memory (no real game data)."""

import struct
import tempfile
import unittest
from pathlib import Path

from xboxport.xbe import ENTRY_POINT_KEYS, KERNEL_THUNK_KEYS, parse_xbe

BASE = 0x00010000
HEADER_OFF = 0x104
CERT_OFF = 0x178
CERT_SIZE = 0xB0
SECT_HEADERS_OFF = CERT_OFF + CERT_SIZE  # 0x228
SECT_HEADER_SIZE = 0x38
NAME_TABLE_OFF = SECT_HEADERS_OFF + SECT_HEADER_SIZE  # one section
SECTION_FILE_OFF = 0x1000
SECTION_DATA = b"\x90" * 0x40


def _pad_utf16_title(title: str) -> bytes:
    raw = title.encode("utf-16-le")
    return (raw + b"\x00" * 80)[:80]


def build_xbe_bytes(entry_kernel: str = "retail", title: str = "TEST GAME") -> bytes:
    entry_virtual = BASE + 0x50
    thunk_virtual = BASE + 0x60
    entry_raw = entry_virtual ^ ENTRY_POINT_KEYS[entry_kernel]
    thunk_raw = thunk_virtual ^ KERNEL_THUNK_KEYS[entry_kernel]

    header_values = [
        BASE,  # base
        0x270,  # size_of_headers
        0x2000,  # size_of_image
        0x178,  # size_of_image_header
        0,  # time_date
        BASE + CERT_OFF,  # certificate_addr
        1,  # number_of_sections
        BASE + SECT_HEADERS_OFF,  # section_headers_addr
        0,  # init_flags
        entry_raw,  # entry_addr_raw
        0, 0, 0, 0, 0, 0, 0, 0,  # tls/pe fields
        0, 0, 0,  # debug paths
        thunk_raw,  # kernel_image_thunk_addr_raw
        0, 0, 0, 0, 0,  # non-kernel import / library versions
        0, 0,  # logo bitmap
    ]
    assert len(header_values) == 29
    header_bytes = struct.pack("<" + "I" * 29, *header_values)

    cert_bytes = struct.pack(
        "<3I 80s 16I 5I",
        CERT_SIZE,
        0,
        0x12345678,
        _pad_utf16_title(title),
        *([0] * 16),
        0,  # allowed_media
        0,  # game_region
        0,  # game_ratings
        1,  # disk_number
        1,  # version
    )

    name_bytes = b".text\x00"
    section_bytes = struct.pack(
        "<9I 20s",
        0,  # flags
        BASE + 0x2000,  # virtual_addr
        len(SECTION_DATA),  # virtual_size
        SECTION_FILE_OFF,  # file_addr
        len(SECTION_DATA),  # file_size
        BASE + NAME_TABLE_OFF,  # name_addr
        0,
        0,
        0,
        b"\x00" * 20,
    )

    buf = bytearray(SECTION_FILE_OFF + len(SECTION_DATA))
    buf[0:4] = b"XBEH"
    buf[HEADER_OFF : HEADER_OFF + len(header_bytes)] = header_bytes
    buf[CERT_OFF : CERT_OFF + len(cert_bytes)] = cert_bytes
    buf[SECT_HEADERS_OFF : SECT_HEADERS_OFF + len(section_bytes)] = section_bytes
    buf[NAME_TABLE_OFF : NAME_TABLE_OFF + len(name_bytes)] = name_bytes
    buf[SECTION_FILE_OFF : SECTION_FILE_OFF + len(SECTION_DATA)] = SECTION_DATA
    return bytes(buf)


class TestXbeParser(unittest.TestCase):
    def _write_and_parse(self, data: bytes):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "default.xbe"
            path.write_bytes(data)
            return parse_xbe(str(path))

    def test_parses_retail_xbe(self):
        info = self._write_and_parse(build_xbe_bytes(entry_kernel="retail", title="MY GAME"))
        self.assertEqual(info.base, BASE)
        self.assertEqual(info.entry_kernel, "retail")
        self.assertEqual(info.entry_addr, BASE + 0x50)
        self.assertEqual(info.kernel_thunk_kernel, "retail")
        self.assertEqual(info.kernel_image_thunk_addr, BASE + 0x60)
        self.assertIsNotNone(info.certificate)
        self.assertEqual(info.certificate.title_name, "MY GAME")
        self.assertEqual(info.certificate.disk_number, 1)
        self.assertEqual(len(info.sections), 1)
        self.assertEqual(info.sections[0].name, ".text")
        self.assertEqual(info.sections[0].file_addr, SECTION_FILE_OFF)
        self.assertEqual(info.sections[0].file_size, len(SECTION_DATA))

    def test_parses_debug_xbe(self):
        info = self._write_and_parse(build_xbe_bytes(entry_kernel="debug"))
        self.assertEqual(info.entry_kernel, "debug")
        self.assertEqual(info.entry_addr, BASE + 0x50)

    def test_rejects_bad_magic(self):
        data = bytearray(build_xbe_bytes())
        data[0:4] = b"NOPE"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.xbe"
            path.write_bytes(bytes(data))
            with self.assertRaises(Exception):
                parse_xbe(str(path))


if __name__ == "__main__":
    unittest.main()
