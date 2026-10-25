#!/usr/bin/env python3
"""Original bounded ARM32 Linux EFI-image inspection; no image execution.

PE/COFF constants follow the UEFI AArch32 binding and upstream efi-header.S.
A valid container is not firmware acceptance, a valid EOS DT, or a safe boot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import lumia


def inspect(data):
    if not 64 <= len(data) <= 64 * 1024 * 1024 or data[:2] != b'MZ':
        raise ValueError('Expected a bounded MZ/PE image')
    pe = struct.unpack_from('<I', data, 60)[0]
    if not 64 <= pe <= len(data) - 24 or data[pe:pe+4] != b'PE\0\0':
        raise ValueError('Invalid PE header bounds/signature')
    machine, count, _, _, _, optional_size, characteristics = struct.unpack_from('<HHIIIHH', data, pe+4)
    optional = pe + 24
    table = optional + optional_size
    if machine != 0x1c2 or not (characteristics & 0x100 and characteristics & 2):
        raise ValueError('Expected UEFI ARMTHUMB_MIXED executable, not ARM64 or another architecture')
    if not 1 <= count <= 16 or optional_size < 96 or table + count * 40 > len(data):
        raise ValueError('Truncated or unsupported PE section table')
    if struct.unpack_from('<H', data, optional)[0] != 0x10b:
        raise ValueError('Expected ARM32 PE32 optional header')
    if struct.unpack_from('<H', data, optional+68)[0] != 10:
        raise ValueError('Expected EFI application subsystem')
    entry = struct.unpack_from('<I', data, optional+16)[0]
    image_size, header_size = struct.unpack_from('<II', data, optional+56)
    if not table + count * 40 <= header_size <= len(data) or header_size > image_size:
        raise ValueError('Invalid PE image/header size')
    sections, raw_ranges, virtual_ranges = [], [], []
    backed_entry = False
    for index in range(count):
        pos = table + index * 40
        name = data[pos:pos+8].split(b'\0')[0].decode('ascii')
        virtual_size, address, raw_size, raw_offset = struct.unpack_from('<IIII', data, pos+8)
        flags = struct.unpack_from('<I', data, pos+36)[0]
        if address + virtual_size > image_size or address < header_size:
            raise ValueError('Section exceeds virtual image bounds')
        if raw_size and (raw_offset < header_size or raw_offset + raw_size > len(data)):
            raise ValueError('Section exceeds backing file bounds')
        for start, end in virtual_ranges:
            if address < end and start < address + virtual_size:
                raise ValueError('Overlapping virtual sections')
        if virtual_size:
            virtual_ranges.append((address, address+virtual_size))
        if raw_size:
            for start, end in raw_ranges:
                if raw_offset < end and start < raw_offset + raw_size:
                    raise ValueError('Overlapping raw sections')
            raw_ranges.append((raw_offset, raw_offset+raw_size))
        # Mixed ARM/Thumb is legal; never require bit0=1 for an ARM-mode EFI entry.
        if address <= (entry & ~1) < address + min(virtual_size, raw_size) and flags & 0x20000000:
            backed_entry = True
        sections.append(dict(name=name, virtual_address=address, virtual_size=virtual_size,
                             raw_offset=raw_offset, raw_size=raw_size, characteristics=flags))
    if not backed_entry:
        raise ValueError('EFI entry is not backed by an executable file section')
    directories = struct.unpack_from('<I', data, optional+92)[0]
    if directories > (optional_size - 96) // 8:
        raise ValueError('Truncated PE data directories')
    certificate = [0, 0]
    if directories > 4:
        certificate = list(struct.unpack_from('<II', data, optional+96+4*8))
        if certificate[1] and certificate[0] + certificate[1] > len(data):
            raise ValueError('Certificate directory exceeds file bounds')
    return dict(result='PASS', bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                machine='ARMTHUMB_MIXED 0x01c2', optional_magic='PE32 0x010b',
                subsystem='EFI application 10', entry_rva=entry, size_of_image=image_size,
                sections=sections, certificate_directory=certificate,
                scope='Container metadata only; no firmware acceptance, signature trust, EOS handoff or hardware validation')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    args = p.parse_args()
    path = lumia.confined(lumia.workpath(''), args.file.resolve())
    if not path.is_file() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('Input is not a bounded regular build artifact')
    print(json.dumps(inspect(path.read_bytes()), indent=2))
