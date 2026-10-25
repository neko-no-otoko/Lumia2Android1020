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

## PMIO and touch: what public sources establish

[Microsoft GPIO documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/bringup/general-purpose-i-o--gpio-)
distinguishes controller-relative and bank-relative numbering.
The [standard GPIO DSM](https://learn.microsoft.com/en-us/windows-hardware/drivers/bringup/gpio-controller-device-specific-method---dsm-)
function 1 returns a package of controller-relative ActiveBoth pins whose initial
asserted polarity is high. If the observed package {0x33} uses that standard GUID
and revision, it names pin 51; it is not a pin-count field or a Linux GPIO number.
The exact GUID/return-type match still needs confirmation from the private source.

The public NT ARM [PMIC GPIO INF](https://github.com/vizPilot/MSM8x60-NT-ARM-Drivers/blob/ba5627f1bb42b174583b14ea225b80c8684a5ca5/msm8x60/Drivers/SOC/PMIC/qcpmicgpio8960.inf)
binds QCOM2038 to qcpmicgpio8960.sys, identifying a driver family. It does not
document the seventeen-field PMIO tuple or prove PM8921 silicon. No PMIO schema
was verified in bounded public searches; search absence is not universal absence.
The inspected INF is an all-rights-reserved reference, not imported driver source.

The official [PMIC GPIO binding](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/Documentation/devicetree/bindings/pinctrl/qcom,pmic-gpio.yaml)
and [SSBI implementation](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/drivers/pinctrl/qcom/pinctrl-ssbi-gpio.c)
use physical GPIO numbers1..44 for PM8921, translated to internal offsets by
subtracting 1. That does not decode the Windows namespace or justify subtracting
192 globally. The actual stock PMIC driver's data decoder is a targeted remaining
static source, not a reason to probe or write handset pins.

Synaptics RMI4 is a reasonable **candidate**, not a confirmed EOS silicon model
or Linux compatible. The EOS-ATT aftermarket INF names it. Another model's
[stock Fame research](https://github.com/samcday/nokia-fame-mainlining/blob/d7920b332a8c26a40cc9d998351081796c15c76b/notes/touch.md)
combines NOKIA_TOUCH and address0x4b with a disabled Synaptics sketch, so 0x4b is
not itself proof of a different vendor. Conversely, a
[OnePlus5 driver INF](https://github.com/edk2-porting/WOA-Drivers/blob/524346372da2091e905164841317f35c35947a82/components/AnySoC/SynapticsTouch-OP5/SynapticsTouch.inf_)
reuses NOKIA_TOUCH for an S3320: that generic identifier cannot identify EOS
silicon. Stock EOS driver/INF/product/function data could narrow this further
statically. No drivers, I2C probes or touch firmware updates were run.

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
| PMIO translation | Windows controller namespace and Linux numbering boundary understood. | Exact stock decoder or vendor schema; may be resolvable statically on the Mini. |
| Touch identity | Synaptics candidate strengthened; generic HID/address insufficient. | Exact stock EOS driver/product/function evidence, potentially later silicon-ID observation if static evidence remains ambiguous. |

These are observations to plan, not instructions to collect them now. Reading
normal-mode phone Info does not provide pre-ExitBootServices memory/GOP state.
Launching even a read-only EFI collector can require a device boot-chain change;
no such delivery, boot, unlock or write is authorized by this research step.
