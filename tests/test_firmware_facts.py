"""Synthetic namespace/bitfield boundaries; no device or vendor code execution."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import firmware_facts as f


class FirmwareFactsTests(unittest.TestCase):
    def setUp(self):
        self.facts = json.loads((Path(__file__).resolve().parents[1] / 'eos-resources.json').read_text())['verified_static']
        self.schema = f.parse_pmio(self.facts['pmio']['arguments'])

    def test_io_irq_namespaces_are_distinct(self):
        self.assertEqual(f.decode_io_pin(self.schema, 234)['windows_index'], 42)
        self.assertEqual(f.decode_io_pin(self.schema, 192)['windows_index'], 0)
        self.assertEqual(f.decode_irq(self.schema, 192)['controller_relative_pin'], 192)
        self.assertEqual(f.decode_irq(self.schema, 51)['controller_relative_pin'], 51)
        with self.assertRaises(ValueError):
            f.decode_io_pin(self.schema, 51)

    def test_pmio_range_boundaries(self):
        self.assertEqual(f.decode_io_pin(self.schema, 139)['windows_index'], 11)
        self.assertEqual(f.linear_pin(self.schema, 4, 15), 271)
        for action in [lambda: f.decode_io_pin(self.schema, 236), lambda: f.decode_io_pin(self.schema, 140),
                       lambda: f.linear_pin(self.schema, 4, 16), lambda: f.linear_pin(self.schema, 0, 64),
                       lambda: f.decode_irq(self.schema, 256)]:
            with self.assertRaises(ValueError):
                action()

    def test_pmio_shape_and_ignored_fields(self):
        args = list(self.facts['pmio']['arguments'])
        args[4] = 12345
        self.assertEqual(f.parse_pmio(args), self.schema)
        for bad in [args[:-1], args + [0], [True] + args[1:], [-1] + args[1:]]:
            with self.assertRaises(ValueError):
                f.parse_pmio(bad)
        args[14] = 192
        with self.assertRaises(ValueError):
            f.parse_pmio(args)

    def test_tlmm_formats_and_pin_limit(self):
        for word in [(151 << 8) | (3 << 4) | 2,
                     (1 << 29) | (151 << 4) | (3 << 21) | 2]:
            result = f.decode_tlmm(word)
            self.assertEqual(result['pin'], 151)
            self.assertEqual(result['function'], 2)
            self.assertEqual(result['output_action'], 'set')
            self.assertEqual(result['config_address'], 0x801970)
            self.assertEqual(result['io_address'], 0x801974)
        for word in [152 << 8, (1 << 29) | (152 << 4), 1 << 32]:
            with self.assertRaises(ValueError):
                f.decode_tlmm(word)

    def test_drive_overlap_is_retained_not_repaired(self):
        result = f.decode_tlmm((1 << 29) | (8 << 17))
        self.assertEqual(result['drive'], 8)
        self.assertEqual(result['direction'], 0)
        self.assertTrue(result['drive_direction_overlap'])
        # Arithmetic cross-check of the reported writer/readback widths only.
        projected_drive_bits = result['drive'] << 6
        self.assertEqual((projected_drive_bits >> 9) & 1, 1)
        self.assertEqual((projected_drive_bits >> 6) & 7, 0)
        self.assertEqual(result['electrical_semantics'], 'unverified')

    def test_only_two_output_nibbles_have_known_actions(self):
        for code in range(16):
            self.assertEqual(f.decode_tlmm(code << 4)['output_action'],
                             {2: 'clear', 3: 'set'}.get(code, 'unspecified'))

    def test_panel_predicate_ignores_high_bits_without_selecting_physical_panel(self):
        for value in [0xc2, 0x00fe00c2, 0xffffffc2]:
            self.assertTrue(f.embedded_tanya_match(value))
        self.assertFalse(f.embedded_tanya_match(0xc3))
        report = f.validate(self.facts)
        self.assertEqual(report['active_panel'], 'unresolved')
        self.assertEqual(report['active_acpi_table'], 'unresolved')
        self.assertEqual(report['shared_rails'], ['LVS4', 'SMPS4'])
        self.assertTrue(report['shared_data_base_differs'])
        self.assertTrue(report['shared_data_offsets_differ'])

    def test_inferred_units_bindings_and_runtime_claims_rejected(self):
        changes = [('pmio', 'linux_binding_status', 'gpio43'), ('pep', 'power_units', 'microvolts'),
                   ('touch_configuration', 'observed_silicon', True),
                   ('display_dispatch', 'physical_panel_observed', True),
                   ('acpi_install', 'general_aml_fixups_proven', True)]
        for section, key, value in changes:
            facts = copy.deepcopy(self.facts)
            facts[section][key] = value
            with self.assertRaises(ValueError):
                f.validate(facts)
        self.facts['pep']['display']['voltage_uv'] = 1800000
        with self.assertRaises(ValueError):
            f.validate(self.facts)


if __name__ == '__main__':
    unittest.main()
