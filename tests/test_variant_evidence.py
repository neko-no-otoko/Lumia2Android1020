"""Synthetic byte comparisons and evidence-scope regressions; no firmware run."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import compare_pe_sections as pe
import variant_evidence
from test_efi_image import fixture


class VariantEvidenceTests(unittest.TestCase):
    def test_header_difference_is_not_whole_file_equality(self):
        left = fixture(); right = bytearray(left); right[72] = 1
        result = pe.compare(left, right)
        self.assertFalse(result['whole_file_equal'])
        self.assertTrue(result['declared_raw_payloads_equal'])
        self.assertEqual(result['behavioral_equivalence'], 'not established')

    def test_changed_data_cannot_be_hidden_by_executable_equality(self):
        left = fixture(); right = bytearray(left); right[0x400] = 1
        result = pe.compare(left, right)
        self.assertTrue(result['executable_payloads_equal'])
        self.assertFalse(result['declared_raw_payloads_equal'])
        right[0x200] = 1
        self.assertFalse(pe.compare(left, right)['executable_payloads_equal'])

    def test_layout_and_executable_flags_are_compared_separately(self):
        left = fixture(); right = bytearray(left)
        struct.pack_into('<I', right, 272+12, 0x2400)
        result = pe.compare(left, right)
        self.assertTrue(result['declared_raw_payloads_equal'])
        self.assertFalse(result['declared_layout_equal'])
        struct.pack_into('<I', right, 272+36, 0xe0000040)
        flags_changed = pe.compare(left, right)
        self.assertFalse(flags_changed['executable_payloads_equal'])
        self.assertTrue(flags_changed['declared_raw_payloads_equal'])

    def test_unbounded_or_overlapping_pe_inputs_rejected(self):
        for mutation in ['truncated', 'raw_overlap', 'virtual_overlap', 'arm64']:
            data = fixture()
            if mutation == 'truncated':
                data = data[:-1]
            elif mutation == 'raw_overlap':
                struct.pack_into('<I', data, 272+20, 0x200)
            elif mutation == 'virtual_overlap':
                struct.pack_into('<I', data, 272+12, 0x1100)
            else:
                struct.pack_into('<H', data, 68, 0xaa64)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                pe.fingerprint(data)

    def test_no_executable_sections_cannot_establish_executable_match(self):
        data = fixture(); struct.pack_into('<I', data, 232+36, 0x40000040)
        result = pe.compare(data, data)
        self.assertTrue(result['whole_file_equal'])
        self.assertFalse(result['executable_payloads_equal'])

    def test_exact_pair_does_not_prove_all_variant_or_runtime_equivalence(self):
        record = json.loads((Path(__file__).resolve().parents[1] / 'rm877-comparison.json').read_text())
        self.assertEqual(variant_evidence.validate(record)['target_product_code'], '059T019')
        for key, value in [('comparison_scope', 'all_eos_variants'), ('runtime_product_dat_observed', True),
                           ('installed_runtime_tables_observed', True), ('target_configuration_emitted', True)]:
            changed = copy.deepcopy(record); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                variant_evidence.validate(changed)
        changed = copy.deepcopy(record); changed['target']['ffu_sha256'] = '0'*64
        with self.assertRaises(ValueError):
            variant_evidence.validate(changed)
        changed = copy.deepcopy(record); changed['target_loader_sha256']['winload.efi'] = '0'*64
        with self.assertRaises(ValueError):
            variant_evidence.validate(changed)

    def test_touch_data_and_changed_uefi_cannot_be_promoted(self):
        record = json.loads((Path(__file__).resolve().parents[1] / 'rm877-comparison.json').read_text())
        for section, key, value in [('touch', 'configuration_carry_forward', True),
                                    ('uefi', 'general_behavior_equivalence', 'verified')]:
            changed = copy.deepcopy(record)
            target = changed['selected_uefi_modules'] if section == 'uefi' else changed['drivers'][section]
            target[key] = value
            with self.assertRaises(ValueError):
                variant_evidence.validate(changed)

    def test_loader_trace_cannot_become_runtime_state_or_observer_approval(self):
        record = json.loads((Path(__file__).resolve().parents[1] / 'rm877-comparison.json').read_text())
        for section, key, value in [('override', 'actual_option_root_values', 'assumed stock root'),
                                    ('override', 'bcd_inspected', True),
                                    ('graphics', 'stock_initialization_passive', True),
                                    ('graphics', 'live_mode_observed', True),
                                    (None, 'live_observer_execution_authorized', True),
                                    (None, 'live_observer_route_accepted', True)]:
            changed = copy.deepcopy(record)
            target = changed['target_loader_review']
            if section:
                target = target[section]
            target[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                variant_evidence.validate(changed)
