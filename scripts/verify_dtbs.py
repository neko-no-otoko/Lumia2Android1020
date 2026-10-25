#!/usr/bin/env python3
"""Compare real compiled DT properties; no hardware or device operations."""
import json
import subprocess
import lumia


def tree(blob):
    tool = lumia.workpath("tools/usr/bin/fdtget")
    env = lumia.build_environment()
    values, nodes, pending = {}, set(), ["/"]
    def query(*args):
        return subprocess.check_output([str(tool), *args], env=env, text=True).split()
    while pending:
        node = pending.pop()
        nodes.add(node)
        for name in query("-p", str(blob), node):
            data = query("-t", "bx", str(blob), node, name)
            values[(node, name)] = bytes(int(byte, 16) for byte in data)
        pending.extend(node.rstrip("/") + "/" + child
                       for child in query("-l", str(blob), node))
    return nodes, values


def verify():
    base = lumia.workpath("build/linux-lumia920/arch/arm/boot/dts/qcom")
    patched = lumia.workpath("build/linux-lumia920-patched/arch/arm/boot/dts/qcom")
    before_nodes, before = tree(base / "lumia920.dtb")
    after_nodes, after = tree(patched / "lumia920.dtb")
    expected = {("/cpus", "#address-cells"): bytes.fromhex("00000001"),
                ("/cpus", "#size-cells"): bytes.fromhex("00000000")}
    if before_nodes != after_nodes or after != before | expected:
        raise ValueError("CPU-cell patch changed more than its two intended properties")
    if any(key in before for key in expected):
        raise ValueError("Baseline unexpectedly already defines CPU cell metadata")
    if tree(base / "lumia920-simple.dtb") != tree(patched / "lumia920-simple.dtb"):
        raise ValueError("Unmodified simple DTB changed")
    print(json.dumps(dict(result="PASS",nodes_compared=len(before_nodes),
                          original_properties_compared=len(before),
                          only_added_properties=["/cpus/#address-cells=1", "/cpus/#size-cells=0"],
                          scope="All other DT nodes and property bytes unchanged; no hardware validation"), indent=2))


if __name__ == "__main__":
    verify()
