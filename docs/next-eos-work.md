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
EOS support or constitute a full binding-schema or hardware test.

Implemented as `patches/0001-lumia920-cpu-cells.patch` in a separate patched source
tree. All 28 nodes and 126 original property byte values are unchanged; only the
two intended properties were added. The original and patched hashes and exact
commands are in `evidence/2026-10-25-cpu-cells.json`.

## Next structural patch: isolate the 920 early-debug assumptions

The baseline modifies generic ARM boot paths with 920-specific behavior:

| Published source | Observed dependency | Feasible source-only preparation |
| --- | --- | --- |
| [head.S](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/arch/arm/kernel/head.S#L307) | Unconditional early framebuffer identity mapping. | Put the experimental path behind an explicit 920 research option; do not infer an EOS address. |
| [mmu.c](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/arch/arm/mm/mmu.c#L1314) | Preserves a hard-coded framebuffer PMD range. | Pair its selection with the early mapping and audit all call paths. |
| [lumiafb.c](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/drivers/video/fbdev/lumiafb.c#L11) | Fixed physical address, geometry and pixel layout. | Separate the debug console from generic boot; future firmware-derived data needs a reviewed handoff implementation. |
| [setup.c](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/arch/arm/kernel/setup.c#L1103) and [init/main.c](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/init/main.c#L1455) | Early-console hooks plus disabled normal init-memory freeing/read-only marking. | Audit lifetime and ordering before restoring either operation; do not blindly uncomment them. |

Implemented separately as `patches/0002-lumia920-debug-option.patch` with
`CONFIG_LUMIA920_EARLY_DEBUG`. It defaults off; the saved 920 defconfig explicitly
enables it to retain the reference path. The patch includes all three EFI-stub
color bars as well as startup writes, mapping/PMD preservation and console hooks.
The separately commented-out init finalization block is unchanged in both modes.

Regression work compares reference-on ARM objects with the original baseline and
checks off-mode objects for removal of each identified hook. Original source and
artifacts stay separate. Successful host compilation or hook removal cannot
establish boot, storage, charging or thermal safety for EOS or for the 920.

The full off-mode link exposed a further caller in `kernel/panic.c`. The third
pinned patch gates its console reactivation, and `panic.o` is now covered by the
paired checks. All of its allocated sections remain unchanged in reference mode.

Checkpoint result: both full modes now link, paired regression passes, and off
vmlinux contains neither early-console entry point. The baseline/reference-on
images are preserved; no kernel build is left running.
See `evidence/2026-10-25-debug-isolation.json` for measured results.

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

## Offline investigation checkpoint

The expanded [offline investigation](eos-offline-research.md) located exact EOS
ACPI/configuration/UEFI package references and validated native static-analysis
tools on synthetic data. Actual package acquisition is blocked by HTTP 403 in
this environment. No EOS board facts have been extracted. Obtain those inputs
before concluding a live phone is necessary; see the staged
[assistance plan](physical-assistance-plan.md).

## Actual stock EOS evidence milestone

The source-input gap above is superseded by [eos-board-evidence.md](eos-board-evidence.md).
An original typed fact inventory, compiled generic-SoC property audit and four
fresh ARM controller-driver object builds now pass. Use its six targeted static
questions before defining an EOS board or enabling peripherals. Memory/handoff,
GPIO translation, mode/power semantics and panel/table selection remain unresolved.
