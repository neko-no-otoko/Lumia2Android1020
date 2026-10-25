#!/usr/bin/env python3
"""Original, data-only checks of reported EOS static findings.

No vendor code is copied. Provenance is in eos-resources.json. These helpers
neither access hardware nor produce Linux bindings or register-write sequences.
"""
import argparse
import json
from pathlib import Path

PMIO_FIELDS = dict(pmic_selector=0, model_value=1, physical_gpio_count=2,
                   physical_gpio_base=3, slot_count=6, bank_width=7,
                   irq_count=9, mpp_count=13, mpp_base=14)
NEW_FIELDS = dict(function=(0, 4), pin=(4, 10), direction=(14, 1),
                  pull=(15, 2), drive=(17, 4), output=(21, 4))
LEGACY_FIELDS = dict(function=(0, 4), pin=(8, 8), direction=(16, 1),
                     pull=(17, 2), drive=(19, 3), output=(4, 4))


def uint(value, bits=32):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('Expected unsigned integer')
    return value


def parse_pmio(arguments):
    if not isinstance(arguments, list) or len(arguments) != 17:
        raise ValueError('PMIO requires exactly 17 arguments')
    for value in arguments:
        uint(value)
    result = {name: arguments[index] for name, index in PMIO_FIELDS.items()}
    if not result['bank_width'] or not result['slot_count'] or not result['irq_count']:
        raise ValueError('Empty PMIO namespace')
    ranges = []
    for name, base, count in [('gpio', result['physical_gpio_base'], result['physical_gpio_count']),
                              ('mpp', result['mpp_base'], result['mpp_count'])]:
        if not count or base + count > result['slot_count']:
            raise ValueError('PMIO I/O range exceeds slot namespace')
        ranges.append((base, base + count, name))
    ranges.sort()
    if ranges[0][1] > ranges[1][0]:
        raise ValueError('Overlapping GPIO/MPP ranges')
    return result


def linear_pin(schema, bank, pin):
    uint(bank)
    uint(pin)
    value = bank * schema['bank_width'] + pin
    if pin >= schema['bank_width'] or value >= schema['slot_count']:
        raise ValueError('Pin outside PMIO slots')
    return value


def decode_io_pin(schema, pin):
    uint(pin)
    for kind, base, count in [('gpio', schema['physical_gpio_base'], schema['physical_gpio_count']),
                              ('mpp', schema['mpp_base'], schema['mpp_count'])]:
        if base <= pin < base + count:
            return dict(kind=kind, windows_index=pin-base, linear_pin=pin)
    raise ValueError('Not a physical GPIO/MPP I/O slot')


def decode_irq(schema, irq):
    uint(irq)
    if irq >= schema['irq_count']:
        raise ValueError('IRQ outside independent interrupt namespace')
    return dict(kind='irq', controller_relative_pin=irq)


def decode_tlmm(word):
    uint(word)
    new = bool(word & (1 << 29))
    fields = NEW_FIELDS if new else LEGACY_FIELDS
    result = {name: (word >> low) & ((1 << width)-1)
              for name, (low, width) in fields.items()}
    if result['pin'] >= 152:
        raise ValueError('DALTLMM rejects pin indices 152 and above')
    # Return observed addresses only, never a write command or electrical setting.
    result.update(format='new' if new else 'legacy',
                  config_address=0x00801000 + 16 * result['pin'],
                  io_address=0x00801004 + 16 * result['pin'],
                  output_action={2: 'clear', 3: 'set'}.get(result['output'], 'unspecified'),
                  drive_direction_overlap=bool(new and result['drive'] & 8),
                  electrical_semantics='unverified')
    return result


def embedded_tanya_match(panel_id):
    """Conditional dispatcher predicate, not physical panel identification."""
    return uint(panel_id) & 0xff == 0xc2


def validate(facts):
    pmio = facts['pmio']
    if pmio['field_indices'] != PMIO_FIELDS or pmio['schema_argument_count'] != 17:
        raise ValueError('Unreviewed PMIO field schema')
    schema = parse_pmio(pmio['arguments'])
    if schema != dict(pmic_selector=0, model_value=8921, physical_gpio_count=44,
                      physical_gpio_base=192, slot_count=272, bank_width=64,
                      irq_count=256, mpp_count=12, mpp_base=128):
        raise ValueError('EOS PMIO facts changed')
    if pmio['linux_binding_status'] != 'unresolved':
        raise ValueError('Windows namespace does not establish a Linux binding')
    tlmm = facts['tlmm']
    expected = dict(pin_count=152, config_base=0x801000, register_stride=16,
                    io_offset=4, input_bit=0, output_bit=1, new_format_selector_bit=29)
    if any(tlmm[key] != value for key, value in expected.items()):
        raise ValueError('Unreviewed TLMM layout')
    for name, fields in [('new_fields', NEW_FIELDS), ('legacy_fields', LEGACY_FIELDS)]:
        if tlmm[name] != {key: list(value) for key, value in fields.items()}:
            raise ValueError('Unreviewed packed TLMM fields')
    if tlmm['writer_positions'] != dict(pull=0, function=2, drive=6, direction=9) or tlmm['readback_drive_bits'] != [6, 3]:
        raise ValueError('Unreviewed writer/readback bit positions')
    dsm = facts['gpio_dsm']
    if (dsm['guid'] != '4f248f40-d5e2-499f-834c-27758ea1cd3f'
            or dsm['function0_buffer'] != [3] or dsm['function1_package'] != [51]):
        raise ValueError('Unreviewed GPIO DSM semantics')
    display = facts['display_dispatch']
    if (display['embedded_tanya_id_low_byte'] != 194 or display['physical_panel_observed'] is not False
            or display['embedded_external_precedence'] != 'unresolved'):
        raise ValueError('Conditional panel dispatch is not observed selection')
    pep = facts['pep']
    if pep['power_units'] != 'strongly_supported_inference' or pep['clock_opcode_semantics'] != 'static_operations_resolved_policy_subenum_unresolved':
        raise ValueError('Raw PEP numbers cannot acquire inferred units/opcodes')
    if set(pep['display']) != {'on_rail_order', 'off_rail_order', 'raw_smps4_level', 'raw_load_fields'}:
        raise ValueError('Unreviewed interpreted power fields')
    touch = facts['touch_configuration']
    if (touch['observed_silicon'] is not False or touch['observed_function_table'] is not False
            or touch['linux_compatible'] != 'unassigned'):
        raise ValueError('Stock configuration is not a silicon/PDT observation')
    install = facts['acpi_install']
    if install['actual_product_dat_read'] is not False or install['general_aml_fixups_proven'] is not False:
        raise ValueError('Do not infer runtime ACPI selection or general fixups')
    layouts = facts['shared_data_layouts']
    # Import here so pep_facts can reuse uint without a module initialization cycle.
    import pep_facts
    return dict(result='PASS', runtime_enablement='none',
                pep=pep_facts.validate(facts),
                display_io=decode_io_pin(schema, 234), dsm_irq=decode_irq(schema, 51),
                gpio192_io=decode_io_pin(schema, 192), irq192=decode_irq(schema, 192),
                shared_rails=sorted(set(pep['display']['on_rail_order']) & set(pep['touch']['rails'])),
                aml_dpid_conditionally_matches_tanya=embedded_tanya_match(0x00fe00c2),
                shared_data_base_differs=layouts['productcfg']['base'] != layouts['ssdt_cdpi']['base'],
                shared_data_offsets_differ=any(layouts['productcfg'][key] != layouts['ssdt_cdpi'][key]
                                              for key in ['product_id_offset', 'panel_id_offset']),
                active_panel='unresolved', active_acpi_table='unresolved')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    facts = json.loads((root / 'eos-resources.json').read_text())['verified_static']
    print(json.dumps(validate(facts), indent=2))


if __name__ == '__main__':
    main()
