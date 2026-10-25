#!/usr/bin/env python3
"""Regression checks on compiled ARM objects; never execute target code."""
import argparse
import difflib
import json
import re
import shutil
import struct
import subprocess
from pathlib import Path
import lumia

FILES = lumia.TARGETS["debug-objects"]


def tool(name, *args):
    return subprocess.check_output([str(lumia.workpath("tools/usr/bin/arm-linux-gnueabihf-" + name)),
                                    *map(str, args)], env=lumia.build_environment(), text=True)


def snapshot(mode, kernel=False):
    output = lumia.workpath("build/linux-lumia920-patched")
    enabled = "CONFIG_LUMIA920_EARLY_DEBUG=y\n" in (output / ".config").read_text()
    if enabled != (mode == "reference"):
        raise ValueError("Snapshot mode does not match the resolved configuration")
    destination = lumia.workpath("regression/debug-" + ("on" if enabled else "off"))
    paths = FILES + ["drivers/firmware/efi/libstub/fdt.o", ".config"]
    if kernel:
        reports = sorted(lumia.workpath("logs").glob(f"patched-{mode}-kernel-*.json"),
                         key=lambda p: p.stat().st_mtime)
        report = json.loads(reports[-1].read_text())
        if report["exit_code"] or report["config_sha256"] != lumia.digest(output / ".config"):
            raise ValueError("No successful full build for this configuration")
        for artifact in report["artifacts"]:
            if lumia.digest(output / artifact["path"]) != artifact["sha256"]:
                raise ValueError("Full-build artifact changed since its report")
        paths += ["vmlinux", "arch/arm/boot/zImage"]
    for path in paths:
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output / path, target)
    (destination / "snapshot.json").write_text(json.dumps(dict(mode=mode, full_kernel=kernel,
        config_sha256=lumia.digest(output / ".config")), indent=2) + "\n")
    print(f"Saved {mode} objects{' and linked kernel' if kernel else ''}: {destination}")


def sections(path):
    data = path.read_bytes()
    if data[:6] != b"\x7fELF\x01\x01":
        raise ValueError("Expected a little-endian ELF32 ARM object")
    offset = struct.unpack_from("<I", data, 32)[0]
    size, count, names_index = struct.unpack_from("<HHH", data, 46)
    rows = [struct.unpack_from("<10I", data, offset + i * size) for i in range(count)]
    names_row = rows[names_index]
    names = data[names_row[4]:names_row[4] + names_row[5]]
    return {names[r[0]:names.find(b"\0", r[0])].decode():
            (data[r[4]:r[4] + r[5]], r[2]) for r in rows if r[1] != 8}


def source_lines(relative):
    before = (lumia.workpath("sources/linux-lumia920") / relative).read_text().splitlines()
    after = (lumia.workpath("sources/linux-lumia920-patched") / relative).read_text().splitlines()
    mapping = {a + i + 1: b + i + 1
               for a, b, n in difflib.SequenceMatcher(a=before, b=after, autojunk=False).get_matching_blocks()
               for i in range(n)}
    return before, mapping


def normalized_init_disassembly(path, reference):
    original, mapping = source_lines("init/main.c")
    reverse = {v: k for k, v in mapping.items()}
    lines = tool("objdump", "-dr", path).splitlines()[2:]
    changed = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"(\s*[0-9a-f]+:)\s+[0-9a-f]+\s+(?:mov|movw)\s+r1,\s*#(\d+)(?:\s+@.*)?", line)
        if not match:
            continue
        number = int(match[2])
        old = reverse.get(number) if reference else number
        if (old in mapping and mapping[old] != old and "WARN(" in original[old - 1]
                and "warn_slowpath_fmt" in "\n".join(lines[index + 1:index + 14])):
            lines[index] = match[1] + f" <WARN source line {old}>"
            changed.append(dict(before=old, after=mapping[old]))
    return lines, changed


def default_off():
    source = lumia.workpath("sources/linux-lumia920-patched")
    output = lumia.workpath("build/linux-lumia920-default-check")
    output.mkdir(parents=True, exist_ok=True)
    baseline = lumia.workpath("build/linux-lumia920/.config").read_text()
    if "LUMIA920_EARLY_DEBUG" in baseline:
        raise ValueError("Default check requires the unmodified baseline config")
    (output / ".config").write_text(baseline)
    with lumia.workpath("logs/debug-default.log").open("w") as log:
        subprocess.run(["make", "-C", str(source), f"O={output}", "ARCH=arm",
                        "CROSS_COMPILE=arm-linux-gnueabihf-", "olddefconfig"],
                       env=lumia.build_environment(), stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    config = (output / ".config").read_text()
    for required in ("CONFIG_ARCH_QCOM=y", "CONFIG_MMU=y", "CONFIG_FB=y", "CONFIG_FONT_8x16=y",
                     "# CONFIG_ARM_LPAE is not set"):
        if required + "\n" not in config:
            raise ValueError("Default check did not satisfy option dependencies")
    if "# CONFIG_LUMIA920_EARLY_DEBUG is not set\n" not in config:
        raise ValueError("Research hooks were enabled by default")
    return "PASS: old baseline config plus new option defaults off with dependencies satisfied"


def verify():
    base = lumia.workpath("build/linux-lumia920")
    on = lumia.workpath("regression/debug-on")
    off = lumia.workpath("regression/debug-off")
    hashes = {label: {p: lumia.digest(root / p) for p in FILES}
              for label, root in [("baseline", base), ("reference", on), ("off", off)]}
    identical = ["arch/arm/kernel/head.o", "arch/arm/mm/mmu.o",
                 "drivers/firmware/efi/libstub/fdt.stub.o"]
    for path in identical:
        if hashes["baseline"][path] != hashes["reference"][path]:
            raise ValueError(f"Reference behavior regression: {path}")
    path = "arch/arm/kernel/setup.o"
    a, b = sections(base / path), sections(on / path)
    for name, (data, flags) in a.items():
        if flags & 2 and name != "__bug_table" and b[name][0] != data:
            raise ValueError(f"Reference setup allocated section changed: {name}")
    _, mapping = source_lines("arch/arm/kernel/setup.c")
    a, b = a["__bug_table"][0], b["__bug_table"][0]
    if len(a) != len(b) or len(a) % 12:
        raise ValueError("Unexpected ARM bug-table format")
    for offset in range(0, len(a), 12):
        x, y = struct.unpack_from("<IIHH", a, offset), struct.unpack_from("<IIHH", b, offset)
        if x[:2] != y[:2] or x[3] != y[3] or mapping.get(x[2]) != y[2]:
            raise ValueError("Setup bug table changed beyond source line metadata")
    old, old_lines = normalized_init_disassembly(base / "init/main.o", False)
    new, new_lines = normalized_init_disassembly(on / "init/main.o", True)
    if old != new or old_lines != new_lines or not old_lines:
        raise ValueError("Reference init code changed beyond verified WARN line immediates")
    a, b = sections(base / "init/main.o"), sections(on / "init/main.o")
    for name, (data, flags) in a.items():
        if flags & 2 and not flags & 4 and b[name][0] != data:
            raise ValueError(f"Reference init allocated data changed: {name}")
    for path, symbol in [("arch/arm/kernel/setup.o", "lumiafb_early_init"),
                         ("init/main.o", "lumiafb_early_deinit")]:
        if symbol not in tool("nm", "-u", on / path) or symbol in tool("nm", "-u", off / path):
            raise ValueError(f"Console hook isolation failed: {symbol}")
    needle = bytes.fromhex("00004080")
    if needle not in (on / FILES[0]).read_bytes() or needle in (off / FILES[0]).read_bytes():
        raise ValueError("Early identity-map literal isolation failed")
    marker = b"Hack: Skipping clearing PMD"
    if marker not in (on / "arch/arm/mm/mmu.o").read_bytes() or marker in (off / "arch/arm/mm/mmu.o").read_bytes():
        raise ValueError("PMD-preservation hook isolation failed")
    for value in (0x0066ff00, 0x00ffff00, 0x00ff0066):
        word = struct.pack("<I", value)
        if word not in (on / "drivers/firmware/efi/libstub/fdt.o").read_bytes() or word in (off / "drivers/firmware/efi/libstub/fdt.o").read_bytes():
            raise ValueError("EFI debug color-bar isolation failed")
    original = (lumia.workpath("sources/linux-lumia920") / "init/main.c").read_text()
    patched = (lumia.workpath("sources/linux-lumia920-patched") / "init/main.c").read_text()
    def finalization(text):
        start = text.index("//system_state = SYSTEM_FREEING_INITMEM;")
        return text[start:text.index("//pti_finalize();", start) + len("//pti_finalize();")]
    if finalization(original) != finalization(patched):
        raise ValueError("Init-memory/read-only overrides were changed")
    result = dict(result="PASS", scope="Compiled-object regression only; no EOS or hardware validation",
                  default_off=default_off(),
                  object_sha256=hashes, reference_byte_identical_objects=identical,
                  setup_change="Only BUG source line metadata / non-allocated symbol strings",
                  init_change="Only verified WARN source-line immediates", warn_line_changes=old_lines,
                  debug_off_checks=["console calls absent", "early framebuffer map literal absent",
                                    "PMD preservation marker absent", "all three EFI color constants absent"],
                  init_memory_and_readonly_overrides="Unchanged; still unresolved in both modes")
    snapshots = [json.loads((p / "snapshot.json").read_text()) for p in (on, off)]
    if all(s["full_kernel"] for s in snapshots):
        for label, root in [("reference", on), ("off", off)]:
            symbols = tool("nm", root / "vmlinux")
            for symbol in ("lumiafb_early_init", "lumiafb_early_deinit"):
                if (symbol in symbols) != (label == "reference"):
                    raise ValueError("Linked-kernel console inclusion mismatch")
        result["linked_kernels"] = {label: {p: lumia.digest(root / p)
            for p in ("vmlinux", "arch/arm/boot/zImage")} for label, root in [("reference", on), ("off", off)]}
    else:
        result["linked_kernels"] = "Not checked in this focused object run"
    lumia.workpath("logs/debug-regression.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["reference", "off", "verify"])
    parser.add_argument("--kernel", action="store_true")
    args = parser.parse_args()
    if args.command == "verify":
        verify()
    else:
        snapshot(args.command, args.kernel)
