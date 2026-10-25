#!/usr/bin/env python3
"""Original host audit of EOS facts against pinned Linux sources. No DTS emission.

Firmware facts are summarized in eos-resources.json; proprietary tables stay private.
This does not assign Linux GPIOs, set clocks/regulators, or execute AML/device code.
"""
import argparse
import collections
import json
import re
import struct
import subprocess
import lumia
import firmware_facts
from verify_dtbs import tree


def validate(data):
    firmware_facts.validate(data['verified_static'])
    if data['variant_gate'] != dict(source_rm='RM-876', source_product_code='059T3B3',
                                    intended_target_rm='RM-875',
                                    actual_handset_rm_product_code_verified=False,
                                    board_equivalence='unverified', target_configuration_emitted=False):
        raise ValueError('RM-876 research cannot establish RM-875 board equivalence')
    if data['schema'] != 1 or data['runtime_enablement'] != 'none':
        raise ValueError('This inventory authorizes no runtime enablement')
    buses = {c['name']: c for c in data['i2c_controllers']}
    if len(buses) != len(data['i2c_controllers']):
        raise ValueError('Duplicate controller identity')
    for controller in buses.values():
        if not 0 < controller['length'] <= 0x10000 or controller['mmio'] % 4:
            raise ValueError('Invalid controller resource bounds')
        if controller['raw_irq'] < 32:
            raise ValueError('Controller IRQ is outside the candidate GIC SPI range')
    seen = set()
    allowed = {'node', 'firmware_hid', 'bus', 'address_7bit', 'bus_hz',
               'gpio_resources', 'linux_status'}
    for peripheral in data['peripherals']:
        if set(peripheral) != allowed or peripheral['linux_status'] != 'unresolved':
            raise ValueError('Unreviewed Linux binding or enablement in factual inventory')
        if peripheral['node'] in seen or peripheral['bus'] not in buses:
            raise ValueError('Duplicate peripheral or unknown bus')
        seen.add(peripheral['node'])
        if not 0x08 <= peripheral['address_7bit'] <= 0x77:
            raise ValueError('Expected an unshifted non-reserved 7-bit I2C address')
        if peripheral['bus_hz'] != 400000:
            raise ValueError('Unexpected firmware bus-rate observation')
        for gpio in peripheral['gpio_resources']:
            if set(gpio) != {'controller', 'pin', 'meaning'} or gpio['pin'] < 0:
                raise ValueError('GPIO provenance/numbering must remain explicit')
            if gpio['controller'] not in {'GIO0', 'PM01'}:
                raise ValueError('Unknown firmware GPIO controller')
    if not data['unknowns'] or data['display']['selection'] != 'unresolved':
        raise ValueError('Missing boot-selection uncertainty')
    if data['boot_template']['cpu_enable_method'] != 'unresolved':
        raise ValueError('Template parking data is not a validated CPU enable method')
    memory = data['template_memory']
    if memory['ram_banks'] != 'unknown' or any('length' in p for p in memory['unsized_pointers']):
        raise ValueError('Do not invent RAM banks or sizes for template pointers')
    regions = sorted(memory['regions'], key=lambda r: r['base'])
    for index, region in enumerate(regions):
        if not 0 < region['length'] or not 0 <= region['base'] < region['base'] + region['length'] <= 2**32:
            raise ValueError('Invalid static region bounds')
        if index and regions[index-1]['base'] + regions[index-1]['length'] > region['base']:
            raise ValueError('Static region overlap requires investigation')


def shared_addresses(data):
    groups = collections.defaultdict(list)
    for p in data['peripherals']:
        groups[p['bus'], p['address_7bit']].append(p['node'])
    return [dict(bus=b, address_7bit=a, firmware_nodes=nodes,
                 interpretation='Shared address; physical-device/driver grouping unresolved')
            for (b, a), nodes in sorted(groups.items()) if len(nodes) > 1]


def compare_resource(firmware, linux_reg, linux_irq):
    # Preserve aperture differences: never rewrite a firmware descriptor to match DT.
    start, size = linux_reg
    if firmware['mmio'] != start:
        raise ValueError('Firmware and Linux controller bases differ')
    if firmware['length'] > size:
        raise ValueError('Firmware aperture exceeds the compared Linux aperture')
    if len(linux_irq) != 3 or linux_irq[0] != 0:
        raise ValueError('Expected a Linux GIC SPI specifier')
    return dict(name=firmware['name'], base=start,
                firmware_length=firmware['length'], linux_length=size,
                length_relation='equal' if firmware['length'] == size else 'firmware-subrange',
                raw_firmware_irq=firmware['raw_irq'], linux_spi_index=linux_irq[1],
                irq_delta=firmware['raw_irq'] - linux_irq[1],
                interpretation='GIC hwirq/SPI-offset hypothesis only; no board IRQ assigned')


def kernel_check(data):
    source = lumia.workpath('sources/linux-lumia920')
    locked, _ = lumia.validate_locks()
    if data['linux_source']['revision'] != locked['revision']:
        raise ValueError('Linux source revision mismatch')
    for name, expected in data['linux_source']['files'].items():
        path = lumia.confined(source, source / name)
        if lumia.digest(path) != expected:
            raise ValueError('Pinned reference changed: ' + name)
    official = data['linux_source']['official_v6_6']
    matched = []
    for entry in official['files']:
        if entry['identical_to_official_v6_6']:
            if data['linux_source']['files'][entry['path']] != entry['official_sha256']:
                raise ValueError('Recorded official upstream fingerprint mismatch')
            matched.append(entry['path'])
    env = lumia.build_environment()
    out = lumia.workpath('eos-resource-audit')
    out.mkdir(parents=True, exist_ok=True)
    dts, dtb = out / 'msm8960-reference.dts', out / 'msm8960-reference.dtb'
    original = source / 'arch/arm/boot/dts/qcom/qcom-msm8960.dtsi'
    commands = [
        ['gcc', '-E', '-nostdinc', '-undef', '-D__DTS__', '-x', 'assembler-with-cpp',
         '-I', str(source / 'include'), str(original), '-o', str(dts)],
        ['dtc', '-I', 'dts', '-O', 'dtb', '-o', str(dtb), str(dts)],
    ]
    log = out / 'compile.log'
    with log.open('w') as stream:
        for cmd in commands:
            subprocess.run(cmd, env=env, check=True, stdout=stream, stderr=stream, timeout=60)
    _, properties = tree(dtb)

    def cells(node, prop):
        raw = properties[node, prop]
        return list(struct.unpack('>' + 'I' * (len(raw) // 4), raw))

    by_name = {c['name']: c for c in data['i2c_controllers'] + data['other_controllers']}
    paths = {'I2C1': '/soc/gsbi@16000000/spi@16080000',
             'SDC1': '/soc/mmc@12400000', 'UFN1': '/soc/usb@12500000',
             'UART5': '/soc/gsbi@16400000/serial@16440000',
             'GIO0': '/soc/pinctrl@800000'}
    comparisons = []
    for name, node in paths.items():
        item = compare_resource(by_name[name], cells(node, 'reg')[:2], cells(node, 'interrupts'))
        item['linux_node'] = node
        item['linux_additional_reg_cells'] = cells(node, 'reg')[2:]
        comparisons.append(item)
    if any(row['irq_delta'] != 32 for row in comparisons):
        raise ValueError('The documented five-controller IRQ correlation no longer holds')
    pinctrl = (source / 'drivers/pinctrl/qcom/pinctrl-msm8960.c').read_text()
    clocks = (source / 'include/dt-bindings/clock/qcom,gcc-msm8960.h').read_text()
    registered = (source / 'drivers/clk/qcom/gcc-msm8960.c').read_text()
    serial = []
    for c in data['i2c_controllers']:
        number = c['gsbi_candidate']
        match = re.search(r'gsbi%d_groups\[\]\s*=\s*\{([^}]+)\}' % number, pinctrl)
        if not match:
            raise ValueError('Missing candidate GSBI pinmux group')
        supported = {int(n) for n in re.findall(r'"gpio(\d+)"', match[1])}
        if not set(c['raw_tlmm_pair']) <= supported:
            raise ValueError('Candidate pins contradict the Linux pinmux group')
        names = [f'GSBI{number}_H_CLK', f'GSBI{number}_QUP_CLK']
        if any(not re.search(r'^#define\s+' + n + r'\s+\d+', clocks, re.M)
               or not re.search(r'\[' + n + r'\]\s*=', registered) for n in names):
            raise ValueError('Candidate clock not defined and registered')
        serial.append(dict(firmware_controller=c['name'], candidate_gsbi=number,
                           pinmux_group_contains_raw_pair=True, linux_clock_names=names,
                           limitation='Corroboration only; GPIO translation, GSBI mode, rates and electrical settings unresolved'))
    return dict(commands=commands, compiled_scope='Unchanged pinned reference-fork MSM8960 DTSI, not official upstream or EOS DTS',
                official_revision=official['official_revision'], official_identical_files=matched,
                fork_dtsi_differences=official['dtsi_differences'],
                dtb_sha256=lumia.digest(dtb), compiler_log_sha256=lumia.digest(log),
                compiler_diagnostics=log.read_text().splitlines(),
                controller_comparisons=comparisons, serial_candidates=serial)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-kernel', action='store_true')
    args = parser.parse_args()
    data = lumia.load_json('eos-resources.json')
    validate(data)
    report = dict(result='PASS', scope='Host resource audit only; no EOS DTS emitted or hardware enabled',
                  source_ffu=data['provenance']['ffu_sha256'],
                  variant_gate=data['variant_gate'],
                  static_decoders=firmware_facts.validate(data['verified_static']),
                  shared_addresses=shared_addresses(data), runtime_enablement='none')
    if args.check_kernel:
        report['kernel_check'] = kernel_check(data)
    path = lumia.workpath('logs/eos-resource-check.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
