"""Synthetic policies, tuple positions and shared-client arithmetic boundaries."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pep_facts as p


class PepFactsTests(unittest.TestCase):
    def test_frequency_units_and_all_policies(self):
        for offset, multiplier in [(0, 1), (4, 1000), (8, 1000000)]:
            rates = [8*multiplier, 12*multiplier]
            self.assertEqual([p.select_frequency(10, offset+i, rates) for i in range(1, 5)],
                             [12*multiplier, 8*multiplier, 8*multiplier, None])
            self.assertEqual(p.select_frequency(12, offset+4, rates), 12*multiplier)
        self.assertEqual(p.frequency_selector(3), dict(unit='Hz', multiplier=1, policy='closest'))

    def test_unavailable_candidates_and_overflow_not_guessed(self):
        self.assertIsNone(p.select_frequency(10, 1, [8]))
        self.assertIsNone(p.select_frequency(10, 2, [12]))
        self.assertIsNone(p.select_frequency(10, 3, []))
        for action in [lambda: p.frequency_selector(0), lambda: p.frequency_selector(13),
                       lambda: p.select_frequency(5000, 11, [1]), lambda: p.select_frequency(1, 3, [True])]:
            with self.assertRaises(ValueError):
                action()

    def test_tlmm_consumer_order_and_bounds(self):
        self.assertEqual(p.tlmm_tuple([50, 3, 2, 1, 0, 8]),
                         dict(pin=50, output=3, function=2, direction=1, pull=0, drive=8))
        for values in [[50, 3, 2, 1, 0], [152, 3, 2, 1, 0, 8], [50, 3, 2, 3, 0, 8]]:
            with self.assertRaises(ValueError):
                p.tlmm_tuple(values)

    def test_vote_type_is_not_enable_flag_and_lengths_are_exact(self):
        for kind, count in [(1, 7), (2, 10), (7, 1)]:
            package = ['SMPS4', kind] + [0]*count
            self.assertEqual(p.parse_vote(package)['resource_type'], kind)
            for bad in [package[:-1], package+[0]]:
                with self.assertRaises(ValueError):
                    p.parse_vote(bad)
        for kind in [0, 3, True]:
            with self.assertRaises(ValueError):
                p.parse_vote(['rail', kind, 0])

    def test_votes_max_and_independent_sums(self):
        rows = [[1800000, 40000, 20000, 0, 0, 0, 0],
                [2850000, 20000, 10000, 0, 0, 0, 0]]
        report = p.aggregate_votes(1, rows)
        self.assertEqual(report['first_field_max'], 2850000)
        self.assertEqual(report['summed_rounded_clamped'], [60, 30])
        self.assertEqual(p.aggregate_votes(1, list(reversed(rows))), report)
        self.assertEqual(p.aggregate_votes(1, [rows[1]])['summed_rounded_clamped'], [20, 10])

    def test_vote_rounding_clamping_and_machine_bounds(self):
        def row(a, b):
            return [1, a, b, 0, 0, 0, 0, 0, 0, 0]
        self.assertEqual(p.aggregate_votes(2, [row(499, 500)])['summed_rounded_clamped'], [0, 1])
        self.assertEqual(p.aggregate_votes(2, [row(1023500, 5000000)])['summed_rounded_clamped'], [1023, 1023])
        for values in [[[2**23]+[0]*9], [row(2**32-1, 0)]]:
            with self.assertRaises(ValueError):
                p.aggregate_votes(2, values)

    def test_cxo_is_shared_or_vote_not_physical_off(self):
        self.assertEqual(p.aggregate_votes(7, [[1], [0]])['aggregated_bit'], 1)
        self.assertEqual(p.aggregate_votes(7, [[0], [0]])['aggregated_bit'], 0)
        self.assertEqual(p.aggregate_votes(7, [])['physical_clock_state'], 'unobserved')
        with self.assertRaises(ValueError):
            p.aggregate_votes(7, [[2]])

    def test_schema_keeps_inference_and_subenum_unresolved(self):
        facts = json.loads((Path(__file__).resolve().parents[1] / 'eos-resources.json').read_text())['verified_static']
        self.assertEqual(p.validate(facts)['vreg_package_lengths'], {'1': 9, '2': 12, '7': 3})
        for section, key, value in [('pep', 'clock_policy_subenum', 'known'),
                                    ('vreg_votes', 'units_status', 'proven'),
                                    ('vreg_votes', 'transport_bytes', 64),
                                    ('pep', 'tlmm_tuple_order', ['pin', 'function', 'direction', 'pull', 'drive', 'output'])]:
            changed = copy.deepcopy(facts)
            target = changed['pep'] if section == 'pep' else changed['pep'][section]
            target[key] = value
            with self.assertRaises(ValueError):
                p.validate(changed)


if __name__ == '__main__':
    unittest.main()
