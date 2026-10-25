# Next source-level work toward EOS

This plan follows the host compile milestone. It proposes no EOS board addresses,
device image, hardware test, Android release or firmware import. Published source
evidence is pinned to `9872e9316212490b7db8e3371fa1d63bd3394cc5`.

## First small patch: correct CPU-node cell metadata

The [tiny 920 device tree](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/arch/arm/boot/dts/qcom/lumia920.dts#L16)
has single-cell CPU `reg` values but no address/size-cell declarations under `cpus`.
The [ARM CPU binding](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/Documentation/devicetree/bindings/arm/cpus.yaml#L65)
describes one-cell CPU identifiers and gives examples with `#address-cells = <1>`
and `#size-cells = <0>`. Adding those declarations is a bounded source-format fix
for the reproduced `reg_format` / default-cell warnings. No peripheral addresses,
RAM ranges, regulators or pin mappings need to change.

Validate a separate patched build against the recorded unmodified DTB: check
warning removal and read back the CPU nodes, model and compatible properties.
Retain both hashes. This would improve the reference source; it would not establish
EOS support or constitute a full binding-schema or hardware test. This patch has
not been applied in the current milestone.

## Next structural patch: isolate the 920 early-debug assumptions

The baseline modifies generic ARM boot paths with 920-specific behavior:

| Published source | Observed dependency | Feasible source-only preparation |
| --- | --- | --- |
| [head.S](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/arch/arm/kernel/head.S#L307) | Unconditional early framebuffer identity mapping. | Put the experimental path behind an explicit 920 research option; do not infer an EOS address. |
| [mmu.c](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/arch/arm/mm/mmu.c#L1314) | Preserves a hard-coded framebuffer PMD range. | Pair its selection with the early mapping and audit all call paths. |
| [lumiafb.c](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/drivers/video/fbdev/lumiafb.c#L11) | Fixed physical address, geometry and pixel layout. | Separate the debug console from generic boot; future firmware-derived data needs a reviewed handoff implementation. |
| [setup.c](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/arch/arm/kernel/setup.c#L1103) and [init/main.c](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/init/main.c#L1455) | Early-console hooks plus disabled normal init-memory freeing/read-only marking. | Audit lifetime and ordering before restoring either operation; do not blindly uncomment them. |

The resulting experiment should retain an explicit current-reference configuration
and add a separate configuration with the 920 debug hooks disabled. Compile both
on the host, checking symbols and diagnostics. Review the EFI stub's color-bar
code as part of the same dependency audit. Default-off isolation is a proposed
design, not an implemented or tested configuration in this milestone.

## Evidence still required for an actual EOS port

[Nokia's published specifications](https://blogs.windows.com/devices/2013/07/11/nokia-lumia-1020-the-smartphone-camera-revolution-begins/)
establish the 1020's display dimensions and RAM capacity. They do not establish
its usable physical-memory ranges, reserved regions, framebuffer address/stride,
GPIO wiring, regulator constraints, thermal controls or UEFI handoff. Do not copy
the 920 ranges or increase a memory-size constant to represent the 1020.

Before writing an EOS DTS, obtain a reusable source/provenance chain or published
board evidence for each missing field. The separate RM-875 pmOS mention remains
a research lead, not that evidence. Android also needs a justified kernel/config,
device product and HAL/vendor ABI/license case. More host storage or a framework
emulator would not supply those dependencies.
