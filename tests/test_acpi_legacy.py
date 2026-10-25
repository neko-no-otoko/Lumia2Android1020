"""Synthetic adjacent legacy records model the observed iasl layout hazard."""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from acpi_legacy import parse_madt


def fixture(records):
    h = bytearray(44)
    h[:4] = b'APIC'
    h.extend(records)
    struct.pack_into('<I', h, 4, len(h))
    h[9] = (-sum(h)) & 255
    return h


def gicc(uid):
    return struct.pack('<BBHIIIIIQQ', 11, 40, 0, uid, uid, 1, 1, 26,
                       0x1000 + uid * 0x1000, 0)


class LegacyMadtTests(unittest.TestCase):
    def test_adjacent_legacy_records_never_become_virtual_addresses(self):
        distributor = struct.pack('<BBHIQII', 12, 24, 0, 0, 0x2000000, 0, 0)
        result = parse_madt(fixture(gicc(0) + gicc(1) + distributor))
        self.assertEqual([r['uid'] for r in result['gicc']], [0, 1])
        self.assertEqual([r['parked_address'] for r in result['gicc']], [0x1000, 0x2000])
        self.assertEqual(result['gicd'][0]['physical_base_address'], 0x2000000)
        for r in result['gicc']:
            self.assertEqual(r['length'], 40)
            self.assertEqual(r['physical_base_address'], 0)
            self.assertFalse(any('virtual' in key for key in r))

    def test_zero_and_truncated_subtable_lengths_rejected(self):
        for raw in (bytes([11, 0]), gicc(0)[:-1]):
            with self.assertRaisesRegex(ValueError, 'bounds'):
                parse_madt(fixture(raw))

    def test_modern_record_not_silently_parsed_as_legacy(self):
        raw = bytearray(gicc(0) + bytes(40)); raw[1] = 80
        with self.assertRaisesRegex(ValueError, 'Only legacy'):
            parse_madt(fixture(raw))

    def test_template_checksum_failure_requires_opt_in_and_is_not_fixed(self):
        raw = fixture(gicc(0)); raw[9] = 0
        self.assertNotEqual(sum(raw) & 255, 0)
        with self.assertRaisesRegex(ValueError, 'template mode'):
            parse_madt(raw)
        before = bytes(raw)
        result = parse_madt(raw, allow_template=True)
        self.assertFalse(result['checksum_valid'])
        self.assertEqual(result['checksum_byte'], 0)
        self.assertEqual(bytes(raw), before)
