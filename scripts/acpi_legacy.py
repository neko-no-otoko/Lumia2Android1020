#!/usr/bin/env python3
"""Original bounded parser for 40-byte legacy GICC records; never executes AML.

Addresses in a static firmware template are not runtime memory-map observations.
No fields introduced after the declared record length are read or synthesized.
"""
import argparse
import json
from pathlib import Path
import struct
import lumia


def parse_madt(data, allow_template=False):
    if len(data) < 44 or len(data) > 1024 * 1024 or data[:4] != b'APIC':
        raise ValueError('Expected a bounded MADT/APIC table')
    length = struct.unpack_from('<I', data, 4)[0]
    if not 44 <= length <= len(data):
        raise ValueError('Invalid MADT declared length')
    valid_checksum = not (sum(data[:length]) & 255)
    if not valid_checksum and not allow_template:
        raise ValueError('Checksum invalid; explicit template mode required for static templates')
    result = dict(declared_length=length, checksum_valid=valid_checksum,
                  checksum_byte=data[9], legacy_header_address=struct.unpack_from('<I', data, 36)[0],
                  scope='Static parsing only; runtime fixups, CPU protocol and vendor authenticity unverified',
                  gicc=[], gicd=[], other_records=[])
    offset = 44
    while offset < length:
        if offset + 2 > length:
            raise ValueError('Truncated subtable header')
        kind, size = data[offset:offset+2]
        if size < 2 or offset + size > length:
            raise ValueError('Subtable exceeds declared bounds')
        record = data[offset:offset+size]
        if kind == 11:
            if size != 40:
                raise ValueError('Only legacy 40-byte GICC supported; do not guess another layout')
            _, _, _, cpu, uid, flags, parking, irq, parked, physical = struct.unpack('<BBHIIIIIQQ', record)
            result['gicc'].append(dict(offset=offset, length=size, cpu_interface=cpu, uid=uid,
                                       flags=flags, parking_protocol=parking, performance_irq=irq,
                                       parked_address=parked, physical_base_address=physical))
        elif kind == 12:
            if size != 24:
                raise ValueError('Only 24-byte GIC distributor record supported')
            result['gicd'].append(dict(offset=offset, length=size,
                                       gic_id=struct.unpack_from('<I', record, 4)[0],
                                       physical_base_address=struct.unpack_from('<Q', record, 8)[0],
                                       system_vector_base=struct.unpack_from('<I', record, 16)[0]))
        else:
            result['other_records'].append(dict(offset=offset, type=kind, length=size))
        offset += size
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    p.add_argument('--template', action='store_true', help='Report invalid checksum as static-template evidence; never fix it')
    args = p.parse_args()
    path = lumia.confined(lumia.workpath('research/private'), args.file.resolve())
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError('Input is not a bounded private regular file')
    print(json.dumps(parse_madt(path.read_bytes(), args.template), indent=2))
