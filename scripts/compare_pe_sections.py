#!/usr/bin/env python3
"""Original bounded ARM PE32 section fingerprint comparison; no code execution.

Format reference: https://learn.microsoft.com/en-us/windows/win32/debug/pe-format
Whole-file, declared payload and executable-only equality are distinct facts.
No signature authentication, behavioral equivalence or hardware support inferred.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import lumia


def fingerprint(data):
    if not 64 <= len(data) <= 64*1024*1024 or data[:2] != b'MZ':
        raise ValueError('Expected bounded MZ/PE data')
    pe = struct.unpack_from('<I', data, 60)[0]
    if not 64 <= pe <= len(data)-24 or data[pe:pe+4] != b'PE\0\0':
        raise ValueError('Invalid PE header')
    machine, count = struct.unpack_from('<HH', data, pe+4)
    optional_size = struct.unpack_from('<H', data, pe+20)[0]
    optional = pe+24
    table = optional+optional_size
    if machine not in (0x1c0, 0x1c2, 0x1c4) or optional_size < 96:
        raise ValueError('Only ARM32 image headers supported')
    if not 1 <= count <= 96 or table+40*count > len(data):
        raise ValueError('Truncated section table')
    if struct.unpack_from('<H', data, optional)[0] != 0x10b:
        raise ValueError('Only PE32 supported')
    image_size, header_size = struct.unpack_from('<II', data, optional+56)
    if not table+40*count <= header_size <= len(data) or header_size > image_size:
        raise ValueError('Invalid header/image size')
    sections, ranges, virtual = [], [], []
    for index in range(count):
        pos = table+40*index
        name = data[pos:pos+8].split(b'\0')[0].decode('ascii')
        size, address, raw_size, raw_offset = struct.unpack_from('<IIII', data, pos+8)
        flags = struct.unpack_from('<I', data, pos+36)[0]
        if address < header_size or address+max(size, raw_size) > image_size:
            raise ValueError('Section outside virtual image')
        if raw_size and (raw_offset < header_size or raw_offset+raw_size > len(data)):
            raise ValueError('Section outside file')
        for start, end in ranges:
            if raw_size and raw_offset < end and start < raw_offset+raw_size:
                raise ValueError('Overlapping raw sections')
        for start, end in virtual:
            if max(size, raw_size) and address < end and start < address+max(size, raw_size):
                raise ValueError('Overlapping virtual sections')
        if raw_size:
            ranges.append((raw_offset, raw_offset+raw_size))
        if max(size, raw_size):
            virtual.append((address, address+max(size, raw_size)))
        sections.append(dict(index=index, name=name, virtual_address=address,
                             virtual_size=size, raw_size=raw_size, raw_offset=raw_offset,
                             flags=flags, executable=bool(flags & 0x20000000),
                             raw_sha256=hashlib.sha256(data[raw_offset:raw_offset+raw_size]).hexdigest()))
    return dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), machine=machine,
                subsystem=struct.unpack_from('<H', data, optional+68)[0], sections=sections)


def compare(reference, target):
    left, right = fingerprint(reference), fingerprint(target)
    def payload(rows):
        return [(row['index'], row['name'], row['raw_size'], row['raw_sha256']) for row in rows]
    all_equal = payload(left['sections']) == payload(right['sections'])
    executable_left = [s for s in left['sections'] if s['executable']]
    executable_right = [s for s in right['sections'] if s['executable']]
    executable_equal = bool(executable_left) and payload(executable_left) == payload(executable_right)
    layout_keys = ('index', 'name', 'virtual_address', 'virtual_size', 'raw_size', 'raw_offset', 'flags')
    layout = lambda rows: [tuple(row[k] for k in layout_keys) for row in rows]
    return dict(reference=left, target=right, whole_file_equal=reference == target,
                declared_raw_payloads_equal=all_equal, executable_payloads_equal=executable_equal,
                declared_layout_equal=layout(left['sections']) == layout(right['sections']),
                behavioral_equivalence='not established', signature_trust='not verified',
                runtime_enablement='none')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    inputs = []
    for value in (args.reference, args.target):
        path = lumia.confined(lumia.workpath(''), value.resolve())
        if not path.is_file() or path.stat().st_size > 64*1024*1024:
            raise ValueError('Input must be a bounded regular private artifact')
        inputs.append(path.read_bytes())
    print(json.dumps(compare(*inputs), indent=2))
