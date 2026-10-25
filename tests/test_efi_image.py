"""Synthetic PE32 fixtures test architecture and backing-file rejection cases."""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_efi_image import inspect


def fixture():
    data = bytearray(0x600)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 64)
    data[64:68] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', data, 68, 0x1c2, 2, 0, 0, 0, 144, 0x102)
    opt = 88
    struct.pack_into('<H', data, opt, 0x10b)
    struct.pack_into('<I', data, opt+16, 0x1000)
    struct.pack_into('<II', data, opt+56, 0x3000, 0x200)
    struct.pack_into('<H', data, opt+68, 10)
    struct.pack_into('<I', data, opt+92, 6)
    for i, name, va, flags in [(0, b'.text', 0x1000, 0x60000020), (1, b'.data', 0x2000, 0xc0000040)]:
        off = 232 + i*40
        data[off:off+len(name)] = name
        struct.pack_into('<IIII', data, off+8, 0x200, va, 0x200, 0x200+i*0x200)
        struct.pack_into('<I', data, off+36, flags)
    return data


class EfiImageTests(unittest.TestCase):
    def test_arm_and_thumb_entry_metadata_both_allowed(self):
        data = fixture()
        self.assertEqual(inspect(data)['entry_rva'], 0x1000)
        struct.pack_into('<I', data, 104, 0x1001)
        self.assertEqual(inspect(data)['entry_rva'], 0x1001)

    def test_other_architecture_and_subsystem_rejected(self):
        for offset, value in [(68, 0xaa64), (68, 0x14c), (156, 3), (88, 0x20b)]:
            data = fixture(); struct.pack_into('<H', data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                inspect(data)

    def test_data_and_unbacked_entry_rejected(self):
        for entry in [0x2000, 0x1800, 0x3000]:
            data = fixture(); struct.pack_into('<I', data, 104, entry)
            with self.subTest(entry=entry), self.assertRaisesRegex(ValueError, 'entry'):
                inspect(data)

    def test_truncated_and_overlapping_sections_rejected(self):
        with self.assertRaisesRegex(ValueError, 'backing file'):
            inspect(fixture()[:-1])
        data = fixture(); struct.pack_into('<I', data, 272+12, 0x1100)
        with self.assertRaisesRegex(ValueError, 'Overlapping virtual'):
            inspect(data)

    def test_header_and_directory_bounds_rejected(self):
        data = fixture(); struct.pack_into('<I', data, 60, len(data)-4)
        with self.assertRaisesRegex(ValueError, 'header bounds'):
            inspect(data)
        data = fixture(); struct.pack_into('<I', data, 180, 100)
        with self.assertRaisesRegex(ValueError, 'directories'):
            inspect(data)
