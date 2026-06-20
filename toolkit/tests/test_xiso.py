"""Tests against a synthetic XISO image built in-memory (no real disc data)."""

import struct
import tempfile
import unittest
from pathlib import Path

from xboxport.xiso import ATTR_DIRECTORY, MAGIC, SECTOR_SIZE, extract_iso, list_iso

ROOT_SECTOR = 40
SUBDIR_SECTOR = 45
AAA_FILE_SECTOR = 50
C_FILE_SECTOR = 55
AAA_CONTENT = b"hello aaa file contents"
C_CONTENT = b"hello c file"


def _pack_entry(left: int, right: int, sector: int, size: int, attrs: int, name: bytes) -> bytes:
    entry = struct.pack("<HHIIBB", left, right, sector, size, attrs, len(name)) + name
    pad = (-len(entry)) % 4
    return entry + b"\xff" * pad


def build_iso_bytes() -> bytes:
    total_sectors = C_FILE_SECTOR + 2
    buf = bytearray(total_sectors * SECTOR_SIZE)

    # Root directory table: "AAA.TXT" (file) and "BBB" (dir), BBB is the tree
    # root with AAA.TXT as its left child so in-order traversal is alphabetical.
    aaa_entry = _pack_entry(0, 0, AAA_FILE_SECTOR, len(AAA_CONTENT), 0, b"AAA.TXT")
    bbb_entry = _pack_entry(0, 0, SUBDIR_SECTOR, SECTOR_SIZE, ATTR_DIRECTORY, b"BBB")

    root_table = bytearray(SECTOR_SIZE)
    root_table[0 : len(bbb_entry)] = bbb_entry
    bbb_word_len = len(bbb_entry) // 4
    root_table[len(bbb_entry) : len(bbb_entry) + len(aaa_entry)] = aaa_entry
    # patch BBB's left pointer to point at AAA.TXT's word offset
    struct.pack_into("<H", root_table, 0, bbb_word_len)
    for i in range(len(bbb_entry) + len(aaa_entry), SECTOR_SIZE):
        root_table[i] = 0xFF

    subdir_table = bytearray(SECTOR_SIZE)
    c_entry = _pack_entry(0, 0, C_FILE_SECTOR, len(C_CONTENT), 0, b"C.BIN")
    subdir_table[0 : len(c_entry)] = c_entry
    for i in range(len(c_entry), SECTOR_SIZE):
        subdir_table[i] = 0xFF

    vol_desc = bytearray(SECTOR_SIZE)
    vol_desc[0:20] = MAGIC
    struct.pack_into("<II", vol_desc, 0x14, ROOT_SECTOR, SECTOR_SIZE)
    vol_desc[0x7EC : 0x7EC + 20] = MAGIC

    def place(sector: int, data: bytes) -> None:
        off = sector * SECTOR_SIZE
        buf[off : off + len(data)] = data

    place(32, vol_desc)
    place(ROOT_SECTOR, bytes(root_table))
    place(SUBDIR_SECTOR, bytes(subdir_table))
    place(AAA_FILE_SECTOR, AAA_CONTENT)
    place(C_FILE_SECTOR, C_CONTENT)
    return bytes(buf)


class TestXisoReader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.iso_path = Path(self.tmp.name) / "game.iso"
        self.iso_path.write_bytes(build_iso_bytes())

    def tearDown(self):
        self.tmp.cleanup()

    def test_list_iso_returns_alphabetical_tree(self):
        entries = list_iso(str(self.iso_path))
        paths = [(e.path, e.is_directory, e.size) for e in entries]
        self.assertIn(("AAA.TXT", False, len(AAA_CONTENT)), paths)
        self.assertIn(("BBB", True, SECTOR_SIZE), paths)
        self.assertIn(("BBB/C.BIN", False, len(C_CONTENT)), paths)

    def test_extract_iso_writes_correct_bytes(self):
        with tempfile.TemporaryDirectory() as out:
            extracted = extract_iso(str(self.iso_path), out)
            self.assertIn("AAA.TXT", extracted)
            self.assertIn("BBB/C.BIN", extracted)
            self.assertEqual((Path(out) / "AAA.TXT").read_bytes(), AAA_CONTENT)
            self.assertEqual((Path(out) / "BBB" / "C.BIN").read_bytes(), C_CONTENT)

    def test_rejects_bad_magic(self):
        bad_path = Path(self.tmp.name) / "bad.iso"
        bad_path.write_bytes(b"\x00" * SECTOR_SIZE * 33)
        with self.assertRaises(Exception):
            list_iso(str(bad_path))


if __name__ == "__main__":
    unittest.main()
