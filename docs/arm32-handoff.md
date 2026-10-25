# ARM32 EFI handoff: resolved contract and EOS gaps

Review date: 2026-10-25. This is source research and inspection of already compiled
reference images. No new boot image, firmware execution, device write, CPU release,
SMC probe or AML evaluation occurred. Further local static inspection uses the
Mac Mini via the parent; no MacBook work is requested.

## A licensed primary-core path exists

The original Linux ARM32 EFI stub is reusable GPL-licensed source. It is a
potential primary-core handoff path **if EOS supplies a compatible, accessible
UEFI environment**; it is not a complete EOS loader/DT or proof of that condition.
No LumiaToy code is needed or imported. File notices and exact source hashes are
recorded in [handoff-references.json](../handoff-references.json).

Fourteen original files were independently compared with official Linux v6.6
commit `ffc253263a1375a65fa6c9f62a893e9767fbebfa`; thirteen match the reference
fork byte-for-byte. The differing libstub/fdt.c adds fixed debug framebuffer
writes and diagnostics already addressed by the existing early-debug option.
This does not remove the other fork limitations documented in
[eos-board-evidence.md](eos-board-evidence.md).

## Do not confuse EFI entry with raw Linux entry

[UEFI 2.10 AArch32](https://uefi.org/specs/UEFI/2.10/02_Overview.html#aarch32-platforms)
specifies an EFI application environment with identity-mapped RAM, MMU and caches
enabled, privileged execution, little-endian interfaces and an aligned stack.
Its entry arguments identify the image handle and system table. This is distinct
from the raw Linux entry contract; disabling translation before calling the EFI
stub is not the intended compliant route.

The [Linux ARM boot contract](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/Documentation/arch/arm/booting.rst)
requires initialized RAM, quiesced DMA, interrupts disabled, appropriate SVC/HYP
mode, MMU/data cache off, r0 zero and r2 pointing at valid aligned boot data. For
DT-only platforms r1 can be all ones. These are architectural requirements,
not a proposed EOS register/state recipe. Exact placement must avoid the kernel,
decompressor, initramfs, firmware and reserved areas; no addresses are invented.

The upstream [ARM32 stub](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/drivers/firmware/efi/libstub/arm32-stub.c),
[PE entry](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/drivers/firmware/efi/libstub/efi-stub-entry.c)
and [decompressor transition](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/arch/arm/boot/compressed/head.S#L1452)
implement allocation, EFI/FDT handoff and CPU/cache transition machinery. The
stub also records CPSR/SCTLR before and after ExitBootServices in a Linux EFI
configuration table. This existing instrumentation may be useful during a later
approved boot; it has not produced EOS observations here.

## Memory, DT and framebuffer handoff

The [ARM EFI documentation](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/Documentation/arch/arm/uefi.rst)
describes EFI system-table and memory-map metadata carried in FDT /chosen.
The stub gets a firmware DT, or can load one when configured, and records the
final EFI map around ExitBootServices. ARM32 Linux still needs the appropriate
DT; merely possessing Windows ACPI tables does not make this kernel enumerate
EOS devices through ACPI.

The inspected upstream libstub/fdt.c ignores command-line `dtb=` unless
`efi_get_secureboot()` explicitly reports disabled; unknown is treated as enabled.
It also checks the firmware DEVICE_TREE_GUID table. Actual EOS DT availability and
trust state are unknown. This is a delivery dependency, not a proposal to bypass
or change Secure Boot.

Use the actual source behavior when interpreting memory: libstub/fdt.c removes
FDT reserve-map entries, and
[EFI reserve_regions](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/drivers/firmware/efi/efi-init.c)
discards DT-derived memblocks and rebuilds usable/reserved memory from EFI
descriptors. Static SMEM/framebuffer/SCM/RFS literals are not a substitute for
GetMemoryMap descriptors and attributes. No guessed RAM bank or reservation
layout is supplied by this project.

[The GOP specification](https://uefi.org/specs/UEFI/2.10/12_Protocols_Console_Support.html#graphics-output-protocol)
provides active framebuffer base/size, pixel format/masks and PixelsPerScanLine.
Stride can exceed visible width; a Blt-only mode has no directly usable linear
framebuffer. Therefore 768 by 1280 and a four-MiB template allocation do not prove
runtime address, format or stride.

Upstream [gop.c](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/drivers/firmware/efi/libstub/gop.c)
and screen_info handling already provide a standard path into the kernel.
The saved config has EFI, EFI_STUB, OF, FB_EFI and SYSFB enabled. SYSFB_SIMPLEFB
and DRM_SIMPLEDRM are off; the legacy EFI framebuffer path is available, so those
options being off does not itself require a fixed-address shim. GOP availability,
firmware framebuffer persistence and safe display power behavior remain untested.

## Secondary cores: reusable references, unresolved EOS adaptation

Official v6.6 [ACPI parking code](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/arch/arm64/kernel/acpi_parking_protocol.c)
is ARM64-specific and depends on its architecture/ACPI integration. The ARM32
tree has no equivalent upstream backend. CONFIG_ARM_PSCI enables code, not proof
that the firmware implements or advertises PSCI. EOS's static FADT flags 0 and
parking version 1 do not justify selecting PSCI or the reference DT's KPSS path.
They also do not prove what runtime-installed tables contain.

A GPL-2.0-only [ARM32 parking port](https://github.com/grate-driver/linux/blob/33fad3cba453102214138ed957ea35cd94601abc/arch/arm/kernel/acpi_parking_protocol.c)
exists. Its [selection helper](https://github.com/grate-driver/linux/blob/33fad3cba453102214138ed957ea35cd94601abc/arch/arm/include/asm/acpi_parking_protocol.h)
is restricted to microsoft,surface-rt-efi. It hard-codes four Surface RT mailboxes
at 0x82001000 through 0x82004000 and changes entry accesses to 32-bit. EOS's two
static records instead name 0x80301000/0x80302000. No code was imported, compiled
as an EOS backend or executed. A generic adaptation needs the actual mailbox
protocol, CPU/GIC identifiers, reserved-memory attributes, ARM entry-state,
cache/order and wakeup semantics; changing address constants would be insufficient.

The [UEFI ACPI document index](https://uefi.org/acpi) links the original ARM
multiprocessor-startup document, but that exact ACPICA DOCX currently redirects
to an Intel404 endpoint through the reader. Its contents were not reviewed here.
The bounded conclusions above rest on the inspected Linux implementations, not
an invented claim of having audited that unavailable specification.

## PMIO and touch: source boundaries

The [static decoder milestone](eos-static-decoders.md) now confirms the stock
17-field PMIO parser, separate I/O and IRQ namespaces, standard GPIO DSM GUID,
and Synaptics3400_EOS intended configuration from the same verified FFU. These
supersede the earlier public-source-only gaps. No raw driver or disassembly is
published, and cloud arithmetic tests do not independently authenticate it.

The official [PMIC GPIO binding](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/Documentation/devicetree/bindings/pinctrl/qcom,pmic-gpio.yaml)
and [SSBI implementation](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/drivers/pinctrl/qcom/pinctrl-ssbi-gpio.c)
use physical GPIO numbers 1..44 for PM8921, translated to internal offsets by
subtracting 1. A Windows GPIO index is not automatically a Linux binding.
Likewise stock F01/F11/F51/F54 configuration labels are not an observed RMI
function table or silicon identity. No I2C probes or firmware updates occurred.

## Host validation and remaining observations

The original [PE inspector](../scripts/check_efi_image.py) validates architecture,
EFI subsystem, table/section bounds, overlapping sections and a file-backed
executable entry. It accepts legal ARM and Thumb entry metadata. It does not
load an image, authenticate signatures or approve deployment.

```sh
python3 scripts/check_efi_image.py .work/build/linux-lumia920/arch/arm/boot/zImage
python3 -m unittest discover -s tests -q
```

All three preserved kernels pass: ARMTHUMB_MIXED 0x01c2, PE32, EFI application 10,
entry RVA 0x77d4. Their certificate directories are empty; firmware acceptance and
trust policy are unknown. Image hashes are unchanged. Five new malformed-image
regression cases bring the local suite to 37 passing tests. Full results and
source fingerprints are in [evidence](../evidence/2026-10-25-handoff.json).

| Question | Static status | Missing observation or source |
| --- | --- | --- |
| Primary-core licensed handoff | Upstream ARM32 EFI stub and contract identified. | Live EOS EFI services, entry state and legal executable acceptance; no delivery/execution path approved here. |
| Usable/reserved memory | Standard map transport/consumption understood; static literals recorded. | Actual GetMemoryMap descriptors, attributes, version/size and reservations, including mailbox/shared/secure/framebuffer regions. |
| Display handoff | Standard GOP/screen_info path and compiled FB_EFI support identified. | Actual protocol/current mode, base/size, scanline stride, pixel format/masks and persistence. |
| Secondary parking | Licensed ARM32 reference exists, but is Surface-specific. | Static EOS protocol/entry/wakeup decoder plus live installed CPU data and initial mailbox state. Releasing a CPU is a later write/test, outside scope. |
| PMIO translation | Stock operation-specific decoder now verified; pure host checks pass. | Linux binding, electrical behavior and PEP consumer semantics remain unresolved. |
| Touch identity | Stock Synaptics3400_EOS product/vendor/function configuration identified. | Actual silicon/PDT observation and supported Linux binding remain unverified. |

These are observations to plan, not instructions to collect them now. Reading
normal-mode phone Info does not provide pre-ExitBootServices memory/GOP state.
Launching even a read-only EFI collector can require a device boot-chain change;
no such delivery, boot, unlock or write is authorized by this research step.
