"""Synthetic format tests only. They do not validate any Lumia hardware facts."""
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import inspect_eos as eos
import research_tools


def cabinet(name, data):
    encoded = name.encode() + b"\0"
    file_table = struct.pack("<IIHHHH", len(data), 0, 0, 0, 0, 0) + encoded
    data_offset = 44 + len(file_table)
    size = data_offset + 8 + len(data)
    header = struct.pack("<4sIIIIIBBHHHHH", b"MSCF", 0, size, 0, 44, 0, 3, 1, 1, 1, 0, 0, 0)
    return header + struct.pack("<IHH", data_offset, 1, 0) + file_table + struct.pack("<IHH", 0, len(data), len(data)) + data


def table():
    data = bytearray(struct.pack("<4sIBB6s8sI4sI", b"DSDT", 36, 2, 0,
                                b"SYNTH ", b"NOTEOS  ", 1, b"TEST", 1))
    data[9] = (-sum(data)) & 255
    return data


class StaticFormatTests(unittest.TestCase):
    def test_cabinet_metadata_and_traversal(self):
        self.assertEqual(eos.cabinet_members(cabinet("ACPI\\dsdt.aml", b"synthetic")), {"ACPI/dsdt.aml": 9})
        for name in ("../escape", "/absolute", "C:\\escape"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Unsafe"):
                eos.cabinet_members(cabinet(name, b"synthetic"))

    def test_bad_cabinet_never_executes_extractor(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "fixture.cab"
            p.write_bytes(cabinet("../escape", b"synthetic"))
            with mock.patch.object(eos.subprocess, "run") as run:
                with self.assertRaises(ValueError):
                    eos.extract_cabinet(p, Path(tmp) / "out")
                run.assert_not_called()

    def test_acpi_checksum_and_length(self):
        raw = table()
        self.assertEqual(eos.acpi_header(raw)["table_id"], "NOTEOS")
        raw[9] ^= 1
        with self.assertRaisesRegex(ValueError, "checksum"):
            eos.acpi_header(raw)
        with self.assertRaises(ValueError):
            eos.acpi_header(b"DSDT")

    def test_static_pcfg_and_unsafe_xml(self):
        def asl(data):
            return 'Name (PCFG, Buffer (0x%x) { %s })' % (len(data), ', '.join('0x%02X' % b for b in data))
        xml = b'<Panel source="synthetic-not-device"/>'
        self.assertEqual(eos.pcfg_buffers(asl(xml))[0]["xml"], xml.decode())
        self.assertEqual(len(eos.pcfg_buffers(asl(xml) + '\n' + asl(xml))), 2)
        with self.assertRaisesRegex(ValueError, "entities"):
            eos.pcfg_buffers(asl(b'<!DOCTYPE x [<!ENTITY y "x">]><x/>'))
        with self.assertRaisesRegex(ValueError, "non-literal"):
            eos.pcfg_buffers('Name (PCFG, Buffer (4) { SOME_METHOD })')

    @unittest.skipUnless((eos.lumia.workpath("research/tools/usr/bin/iasl")).exists(), "Native research tools not installed")
    def test_native_cab_and_iasl_roundtrip_synthetic_only(self):
        with tempfile.TemporaryDirectory(dir=eos.lumia.workpath("research")) as tmp:
            root = Path(tmp)
            xml = b'<Panel source="synthetic-not-device"/>'
            bytes_list = ', '.join('0x%02X' % b for b in xml)
            source = root / "synthetic.asl"
            source.write_text('DefinitionBlock ("", "DSDT", 2, "SYNTH", "NOTEOS", 1) { Name (PCFG, Buffer () { '+bytes_list+' }) }\n')
            env = research_tools.environment()
            subprocess.run(['iasl', '-p', str(root / 'synthetic'), str(source)], env=env, check=True, capture_output=True)
            aml = (root / 'synthetic.aml').read_bytes()
            self.assertEqual(eos.acpi_header(aml)['table_id'], 'NOTEOS')
            cab = root / 'synthetic.cab'; cab.write_bytes(cabinet('ACPI/dsdt.aml', aml))
            extracted = root / 'extracted'
            eos.extract_cabinet(cab, extracted)
            self.assertEqual((extracted / 'ACPI/dsdt.aml').read_bytes(), aml)
            prefix = root / 'decompiled'
            subprocess.run(['iasl', '-d', '-p', str(prefix), str(extracted / 'ACPI/dsdt.aml')], env=env, check=True, capture_output=True)
            parsed = eos.pcfg_buffers((root / 'decompiled.dsl').read_text())
            self.assertEqual(parsed[0]['xml'], xml.decode())


if __name__ == '__main__':
    unittest.main()
