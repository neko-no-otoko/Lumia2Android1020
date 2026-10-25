"""Reject unsafe interpretations of factual EOS resources before future DT work."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import eos_resources as eos
import lumia


class EosResourceTests(unittest.TestCase):
    def setUp(self):
        self.data = lumia.load_json('eos-resources.json')

    def test_shared_als_proximity_address_is_not_two_independent_devices(self):
        eos.validate(self.data)
        shared = eos.shared_addresses(self.data)
        self.assertEqual([(x['bus'], x['address_7bit'], x['firmware_nodes']) for x in shared],
                         [('IC12', 0x39, ['ALS1', 'PRX1'])])

    def test_shifted_i2c_address_rejected(self):
        self.data['peripherals'][0]['address_7bit'] = 0x4b << 1
        with self.assertRaisesRegex(ValueError, '7-bit'):
            eos.validate(self.data)

    def test_implicit_linux_gpio_or_driver_assignment_rejected(self):
        for key, value in [('linux_gpio', 198), ('compatible', 'unverified,driver')]:
            data = copy.deepcopy(self.data)
            data['peripherals'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'Unreviewed Linux binding'):
                eos.validate(data)

    def test_runtime_enablement_rejected(self):
        self.data['runtime_enablement'] = 'enabled'
        with self.assertRaisesRegex(ValueError, 'no runtime enablement'):
            eos.validate(self.data)

    def test_rm876_facts_do_not_establish_rm877_target_equivalence(self):
        for key, value in [('board_equivalence', 'verified'), ('source_rm', 'RM-877'),
                           ('target_configuration_emitted', True)]:
            data = copy.deepcopy(self.data)
            data['variant_gate'][key] = value
            with self.assertRaisesRegex(ValueError, 'board equivalence'):
                eos.validate(data)

    def test_static_pointers_and_ram_are_not_promoted_to_reservations(self):
        self.data['template_memory']['unsized_pointers'][0]['length'] = 4096
        with self.assertRaisesRegex(ValueError, 'invent RAM'):
            eos.validate(self.data)

    def test_overlapping_static_regions_need_review(self):
        self.data['template_memory']['regions'][1]['base'] = 0x80001000
        with self.assertRaisesRegex(ValueError, 'overlap'):
            eos.validate(self.data)

    def test_aperture_difference_is_preserved(self):
        f = dict(name='synthetic', mmio=0x1000, length=0x800, raw_irq=136)
        result = eos.compare_resource(f, [0x1000, 0x8000], [0, 104, 4])
        self.assertEqual(result['length_relation'], 'firmware-subrange')
        self.assertEqual(result['firmware_length'], 0x800)
        self.assertEqual(result['irq_delta'], 32)
        with self.assertRaises(ValueError):
            eos.compare_resource(f, [0x2000, 0x8000], [0, 104, 4])
        with self.assertRaises(ValueError):
            eos.compare_resource(f, [0x1000, 0x100], [0, 104, 4])


if __name__ == '__main__':
    unittest.main()
