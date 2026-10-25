#!/usr/bin/env python3
"""Private, data-only CAB/ACPI inspection. Never execute firmware or evaluate AML."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
import lumia
import research_tools

MAX_CAB = 100 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024


def cabinet_members(data):
    if len(data) < 36 or len(data) > MAX_CAB or data[:4] != b"MSCF":
        raise ValueError("Expected a bounded standalone CAB")
    length, offset = struct.unpack_from("<I", data, 8)[0], struct.unpack_from("<I", data, 16)[0]
    count, flags = struct.unpack_from("<HH", data, 28)
    if not 36 <= offset < length <= len(data) or count > 2000 or flags & 3:
        raise ValueError("Invalid/spanned cabinet or oversized file list")
    result, total = {}, 0
    for _ in range(count):
        if offset + 16 > length:
            raise ValueError("Truncated cabinet member")
        size, _, _, _, _, attrs = struct.unpack_from("<IIHHHH", data, offset)
        offset += 16
        end = data.find(b"\0", offset, min(offset + 2049, length))
        if end < 0:
            raise ValueError("Unterminated cabinet filename")
        name = data[offset:end].decode("utf-8" if attrs & 128 else "cp1252").replace("\\", "/")
        path = PurePosixPath(name)
        if not name or path.is_absolute() or ".." in path.parts or ":" in name or attrs & 0x400:
            raise ValueError("Unsafe cabinet member path/type")
        if str(path) in result:
            raise ValueError("Duplicate cabinet member")
        result[str(path)] = size
        total += size
        if total > MAX_EXPANDED:
            raise ValueError("Cabinet expansion exceeds analysis budget")
        offset = end + 1
    return result


def extract_cabinet(cabinet, destination):
    if cabinet.stat().st_size > MAX_CAB:
        raise ValueError("Cabinet input exceeds analysis budget")
    members = cabinet_members(cabinet.read_bytes())
    destination = lumia.confined(lumia.ROOT, destination)
    if destination.exists():
        raise ValueError("Preserve previous extraction; destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        subprocess.run(["cabextract", "-q", "-d", tmp, str(cabinet.resolve())],
                       env=research_tools.environment(), check=True, timeout=60)
        actual = {}
        for p in Path(tmp).rglob("*"):
            if p.is_symlink():
                raise ValueError("Unexpected extraction symlink")
            if p.is_file():
                actual[str(p.relative_to(tmp))] = p.stat().st_size
                p.chmod(0o600)
        if actual != members:
            raise ValueError("Extracted cabinet differs from its reviewed member metadata")
        Path(tmp).rename(destination)
    return members


def acpi_header(data):
    if len(data) < 36:
        raise ValueError("Truncated ACPI header")
    signature, length, revision, _, oem, table, oem_revision, compiler, compiler_revision = struct.unpack_from(
        "<4sIBB6s8sI4sI", data)
    if signature not in {b"DSDT", b"SSDT"} or not 36 <= length <= len(data) or length > MAX_EXPANDED:
        raise ValueError("Not a bounded DSDT/SSDT table")
    if sum(data[:length]) & 255:
        raise ValueError("ACPI table checksum mismatch")
    return dict(signature=signature.decode(), length=length, revision=revision,
                oem_id=oem.decode("ascii").rstrip("\0 "), table_id=table.decode("ascii").rstrip("\0 "),
                oem_revision=oem_revision, compiler=compiler.decode("ascii"),
                compiler_revision=compiler_revision)


def pcfg_buffers(text):
    if len(text) > 8 * 1024 * 1024:
        raise ValueError("Decompiled ACPI text exceeds budget")
    # This only recognizes static hex-byte buffers, never evaluates ASL methods.
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    pattern = r"Name\s*\(\s*PCFG\s*,\s*Buffer\s*\(\s*(0x[0-9a-fA-F]+|[0-9]+)\s*\)\s*\{([^{}]*)\}\s*\)"
    result = []
    for match in re.finditer(pattern, text):
        length = int(match[1], 0)
        if not 1 <= length <= 128 * 1024:
            raise ValueError("PCFG length exceeds budget")
        tokens = [t.strip() for t in match[2].split(",") if t.strip()]
        if any(not re.fullmatch(r"0x[0-9a-fA-F]{1,2}", token) for token in tokens):
            raise ValueError("Unsupported non-literal PCFG data")
        data = bytes(int(t, 16) for t in tokens)
        if len(data) > length:
            raise ValueError("PCFG initializer exceeds declared length")
        data = data.ljust(length, b"\0").rstrip(b"\0")
        if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
            raise ValueError("XML declarations/entities are not allowed")
        root = ET.fromstring(data)
        result.append(dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                           root_tag=root.tag, xml=data.decode("utf-8")))
    return result


def inspect(package, cabinet):
    # All private inputs/outputs stay below ignored .work/, never mounted or run.
    cabinet = lumia.confined(lumia.workpath("research/private"), cabinet)
    entry = next(e for e in lumia.load_json("firmware-references.json")["packages"] if e["id"] == package)
    if cabinet.stat().st_size > MAX_CAB:
        raise ValueError("Cabinet input exceeds analysis budget")
    data = cabinet.read_bytes()
    if hashlib.sha1(data).hexdigest() != entry["expected_sha1"]:
        raise ValueError("File does not match the exact indexed package digest")
    destination = lumia.workpath("research/private") / (package + "-extracted")
    members = extract_cabinet(cabinet, destination)
    tables = []
    for path in destination.rglob("*"):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if raw[:4] not in {b"DSDT", b"SSDT"}:
            continue
        header = acpi_header(raw)
        prefix = path.with_suffix("")
        subprocess.run(["iasl", "-d", "-p", str(prefix), str(path)],
                       env=research_tools.environment(), cwd=destination, check=True, timeout=60)
        dsdt = Path(str(prefix) + ".dsl")
        buffers = pcfg_buffers(dsdt.read_text())
        tables.append(dict(path=str(path.relative_to(destination)), header=header,
                           pcfg=[{k: v for k, v in b.items() if k != "xml"} for b in buffers]))
    report = dict(scope="Private static inspection only; no firmware execution or handset validation",
                  package=package, sha1=entry["expected_sha1"], sha256=hashlib.sha256(data).hexdigest(),
                  files=len(members), tables=tables,
                  authenticity="Indexed digest match, not independent vendor-signature verification")
    (destination / "private-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", choices=["acpi-eos", "productconfig-eos", "uefi-eos"])
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    inspect(args.package, args.file.resolve())
