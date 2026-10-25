#!/usr/bin/env python3
"""Original data-only models of reported QCpep8960 static semantics.

Provenance: eos-resources.json verified_static. No vendor code is copied or run.
Synthetic candidates/votes are not measured clocks, Linux policy or power safety.
"""
from firmware_facts import uint

CLOCK_OPERATIONS = {
    1: 'enable', 2: 'disable', 3: 'set_frequency', 4: 'invert_with_argument_1',
    5: 'assert_then_deassert_reset', 6: 'external_source_selection',
    7: 'set_divider_when_nonzero', 8: 'enable_then_set_frequency',
    9: 'configuration_policy_subenum_unresolved', 10: 'assert_reset',
    11: 'deassert_reset',
}
TLMM_TUPLE = ('pin', 'output', 'function', 'direction', 'pull', 'drive')
PARAMETER_COUNTS = {1: 7, 2: 10, 7: 1}


def frequency_selector(selector):
    uint(selector)
    if not 1 <= selector <= 12:
        raise ValueError('Unknown frequency selector')
    return dict(unit=('Hz', 'kHz', 'MHz')[(selector-1)//4],
                multiplier=(1, 1000, 1000000)[(selector-1)//4],
                policy=('at_least', 'at_most', 'closest', 'exact')[(selector-1)%4])


def select_frequency(value, selector, candidate_hz):
    """Arithmetic policy demonstration over caller-supplied synthetic candidates."""
    uint(value)
    mode = frequency_selector(selector)
    if not isinstance(candidate_hz, (list, tuple)):
        raise ValueError('Expected explicit candidate list')
    for rate in candidate_hz:
        uint(rate)
    rates = sorted(set(candidate_hz))
    requested = value * mode['multiplier']
    if requested >= 2**32:
        raise ValueError('Conversion overflow behavior not established')
    policy = mode['policy']
    if policy == 'closest':
        return min(rates, key=lambda rate: (abs(rate-requested), rate), default=None)
    if policy == 'exact':
        return requested if requested in rates else None
    matches = [rate for rate in rates if rate >= requested] if policy == 'at_least' else [rate for rate in rates if rate <= requested]
    return (min(matches) if policy == 'at_least' else max(matches)) if matches else None


def tlmm_tuple(values):
    if not isinstance(values, (list, tuple)) or len(values) != 6:
        raise ValueError('TLMM tuple requires six items')
    for value, limit in zip(values, [152, 16, 16, 2, 4, 16]):
        uint(value)
        if value >= limit:
            raise ValueError('TLMM value outside observed packed-field domain')
    return dict(zip(TLMM_TUPLE, values))


def csi_parent_selection(value):
    """Logical two-mux relation only; never an MMCC write sequence."""
    uint(value)
    if value not in (1, 2, 3):
        raise ValueError('Only the statically corroborated CSI subset is modeled')
    return dict(a=int(value == 2), b=int(value == 3), linux_parent_index=value-1,
                fitted_sensor='unobserved')


def aggregate_switch_votes(client_parameters):
    """Type4 LVS enable/pull-down OR only; pin routing and HPM stay literal."""
    rows = []
    for values in client_parameters:
        if not isinstance(values, (list, tuple)) or len(values) not in (4, 5):
            raise ValueError('LVS needs four fields and optional HPM')
        for value in values:
            uint(value)
        if values[0] > 1 or values[1] > 1:
            raise ValueError('LVS enable/pull-down are one-bit votes')
        rows.append(values)
    return dict(enable_vote=int(any(row[0] for row in rows)),
                pull_down_vote=int(any(row[1] for row in rows)),
                physical_rail_state='unobserved', pin_routing_and_hpm='literal; not modeled')


def parse_vote(package):
    """First item stays an opaque resource identifier; second is resource type."""
    if not isinstance(package, (list, tuple)) or len(package) < 2:
        raise ValueError('Missing vote resource/type')
    kind = uint(package[1])
    if kind not in PARAMETER_COUNTS or len(package) != PARAMETER_COUNTS[kind]+2:
        raise ValueError('Unknown resource type or wrong vote length')
    for value in package[2:]:
        uint(value)
    if kind == 7 and package[2] not in (0, 1):
        raise ValueError('CXO vote must be one bit')
    return dict(resource=package[0], resource_type=kind, raw_parameters=list(package[2:]))


def aggregate_votes(resource_type, client_parameters):
    """Aggregate one resource's explicit client snapshot, with no device effect.

    LDO/SMPS: model only the first three fields. Remaining mode flags stay raw.
    Reject inputs beyond representable ranges/unknown machine overflow behavior.
    """
    if type(resource_type) is not int or resource_type not in PARAMETER_COUNTS:
        raise ValueError('Unknown resource type')
    rows = []
    for values in client_parameters:
        rows.append(parse_vote(['synthetic-resource', resource_type, *values])['raw_parameters'])
    if resource_type == 7:
        return dict(resource_type=7, aggregated_bit=int(any(row[0] for row in rows)),
                    physical_clock_state='unobserved')
    if any(row[0] >= 2**23 for row in rows):
        raise ValueError('First field outside modeled 23-bit domain')
    sums = [sum(row[index] for row in rows) for index in (1, 2)]
    if any(value + 500 >= 2**32 for value in sums):
        raise ValueError('Sum overflow behavior not established')
    return dict(resource_type=resource_type,
                first_field_max=max((row[0] for row in rows), default=0),
                summed_rounded_clamped=[min((value+500)//1000, 1023) for value in sums],
                packed_field_widths=[23, 10, 10],
                remaining_mode_flags='literal; not modeled',
                units='microvolt/microamp labels statically corroborated; runtime unobserved',
                runtime_enablement='none')


def validate(facts):
    pep = facts['pep']
    if pep['clock_operations'] != {str(key): value for key, value in CLOCK_OPERATIONS.items()}:
        raise ValueError('Unreviewed clock operation map')
    if pep['tlmm_tuple_order'] != list(TLMM_TUPLE):
        raise ValueError('TLMM tuple order must follow the consumer')
    if pep['frequency_selectors'] != {
            '1-4': 'Hz', '5-8': 'kHz', '9-12': 'MHz',
            'within_each_group': ['at_least', 'at_most', 'closest', 'exact'],
            'closest_tie': 'lower', 'runtime_rates_observed': False}:
        raise ValueError('Unreviewed frequency units/policy or runtime claim')
    vote = pep['vreg_votes']
    if vote['parameter_counts_after_type'] != {str(key): value for key, value in PARAMETER_COUNTS.items()}:
        raise ValueError('Unreviewed regulator vote lengths')
    if (vote['transport_bytes'] != 60 or vote['transport_ioctl'] != '0x80060fd4'
            or vote['aggregation_types1_2'] != {
                'first_field': 'maximum per-client value',
                'next_two_fields': 'independently sum; round (sum+500)//1000; clamp1023',
                'packed_widths': [23, 10, 10]}):
        raise ValueError('Unreviewed vote transport or aggregation schema')
    if (pep['clock_policy_subenum'] != 'stock_CSI_subset_resolved_other_values_unresolved' or vote['units_status'] != 'corroborated_static'
            or vote['other_mode_flags'] != 'literal; unresolved'):
        raise ValueError('Do not promote unresolved/inferred PEP semantics')
    return dict(clock_operation_count=len(CLOCK_OPERATIONS), selector3=frequency_selector(3),
                tlmm_tuple_order=list(TLMM_TUPLE), vreg_package_lengths={str(k): v+2 for k, v in PARAMETER_COUNTS.items()},
                vote_transport_bytes=60, vote_transport_ioctl='0x80060fd4',
                vote_units='statically corroborated labels; runtime unobserved', runtime_enablement='none')
