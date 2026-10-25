# EOS board evidence and Linux cross-check

Review date: 2026-10-25. This is an original factual summary and host audit, not
an EOS DTS, boot image or claim of hardware support. No firmware disassembly,
raw AML, panel XML, provisioning or device identifiers are published.

## Provenance and what changed

The user-supplied stock-style RM-876 / 059T3B3 firmware package identifies build
3051.50009.1424.0004. The parent/local static task inspected the exact FFU:
1,826,881,536 bytes; CRC32 `41ae158c` matches its VPL; SHA-256
`200c402351e7b488fd320bc944a7ab8f1dde2522eac5e7c203584852f541ef08`.
The parent reports all 13,934 embedded SHA-256 chunks and GPT CRCs pass, and EOS
metadata/platform `Nokia.MSM8960.P5217`. These checks establish consistency, not
vendor trust-chain authentication. The mirror and filename alone are insufficient.

The local task extracted 16 board-description files privately and disassembled
DSDT, 2SDT and SSDT using official ACPICA 20260930, with each iasl exit 0 and no
AML execution. This cloud did not materialize that private bundle: its Library
transfer failed. The factual inventory explicitly attributes the source findings
to the parent/local inspection; cloud checks below independently use the pinned
Linux source. No inference of parity with other EOS variants is made.

The previous absence of board-description input is superseded by those actual
stock facts. Missing runtime selections, memory/handoff and resource semantics
remain distinct unresolved questions.

## Facts preserved without assigning Linux bindings

[eos-resources.json](../eos-resources.json) records original selected facts,
units, source hashes and uncertainties. I2C addresses are unshifted seven-bit
addresses at 400 kHz. GPIO values are decimal pins in named **firmware** controller
namespaces; they are not Linux GPIO numbers.

| Firmware function | Bus/address | Firmware identity / unresolved interpretation |
| --- | --- | --- |
| Touch | I2C3 / 0x4b | NOKIA_TOUCH. Stock Synaptics3400_EOS configuration now identified; live silicon/PDT and Linux binding remain unverified. |
| NFC | IC10 / 0x2b | NXP_NFCC; resource and power semantics still needed. |
| Accelerometer | IC12 / 0x1e | KXTNK, not a confirmed Linux compatible. |
| Ambient light and proximity | IC12 / 0x39 | ALS1 and PRX1 share address and IRQ49; do not emit two independent physical I2C devices blindly. |
| Gyro / magnetometer / barometer | IC12 / 0x68, 0x0f, 0x5d | Firmware identities recorded; no driver bindings assigned. |
| IHF | I2C1 / 0x34 | MAXIMUS and raw GPIO resources recorded; no Linux implementation asserted. |

The shared 4,262-byte PCFG describes Tanya; EFIESP PTANYA.XML describes Jessica.
Both report 768 by 1280, four DSI lanes and a 59.71 MHz pixel clock. These shared
values do not resolve panel selection or make initialization sequences interchangeable.
DSDT/2SDT differences include touch IO50, display dependencies and thermal TZ11.
The selected table variant at boot is not established. Power tuple names are
literal observations only, not regulator bindings, voltage values or safe sequences.

## Independent Linux audit

The checker compiles the **unchanged pinned reference-fork MSM8960 DTSI**, reads its
actual DTB properties, verifies per-file source hashes and compares selected facts
against Linux source/bindings at commit
[9872e9316212490b7db8e3371fa1d63bd3394cc5](https://github.com/UEFI-code/linux-6.6-lumia920/tree/9872e9316212490b7db8e3371fa1d63bd3394cc5).
This is a dtc/property comparison, not full binding-schema validation.

| Resource | Comparison with pinned Linux | Consequence |
| --- | --- | --- |
| I2C1 / 0x16080000 | Linux represents this shared QUP block as a disabled SPI child under GSBI1; ACPI reports I2C. Apertures are 0x800 versus 0x1000. | Matching MMIO cannot choose protocol mode; no SPI/I2C activation or aperture rewrite is made. |
| SDC1 / 0x12400000 | ACPI length 0x800 versus Linux 0x8000. | Preserve the discrepancy; no storage driver enabled or writes attempted. |
| UFN1 / 0x12500000 | First 0x200-byte window matches; Linux also describes a second window. ACPI operation-region length is a separate 0x1000 observation. | Do not conflate resource windows and operation regions or infer USB role/charging. |
| UART5 / 0x16440000 | ACPI length 0x100 versus Linux 0x1000 plus a second GSBI region. | Do not infer console enablement from base-address agreement. |
| Five raw controller IRQs | Each equals the compared Linux SPI index plus 32. | Correlates with the GIC offset convention; controller IRQ flags/firmware GSI semantics still need confirmation before an EOS DT assignment. |
| GIO0 / 0x00800000 | Firmware length 0x2000 versus Linux TLMM 0x4000; raw IRQ48 versus SPI16. | Same-base and +32 correlation, not a firmware-pin translation proof. |
| GSBI1/3/10/12 pin pairs | Each pair occurs in the respective Linux pinmux group. Corresponding H/QUP clock IDs are defined and registered. | Candidate corroboration; not GPIO translation, electrical settings, clock rates or safe mode selection. |

Relevant original Linux references are the
[SoC DTSI](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/arch/arm/boot/dts/qcom/qcom-msm8960.dtsi),
[GSBI binding](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/Documentation/devicetree/bindings/soc/qcom/qcom,gsbi.yaml),
[QUP I2C binding](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/Documentation/devicetree/bindings/i2c/qcom,i2c-qup.yaml),
[GIC translation](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/drivers/irqchip/irq-gic.c#L1084),
and [pinmux implementation](https://github.com/UEFI-code/linux-6.6-lumia920/blob/9872e9316212490b7db8e3371fa1d63bd3394cc5/drivers/pinctrl/qcom/pinctrl-msm8960.c).
The QUP binding lists v1.1.1 for MSM8960. No source or raw firmware was copied
into a new driver. Native compilation artifacts remain ignored.

## Official upstream comparison and fork limitations

Eight files were independently retrieved from official
[Linux v6.6](https://github.com/torvalds/linux/tree/ffc253263a1375a65fa6c9f62a893e9767fbebfa).
Pinmux, GCC, GIC translation, the clock IDs and all three audited bindings match
the fork byte-for-byte. Their official hashes are recorded in the inventory and
checked against the pinned source in CI. This is a fingerprint check against
recorded upstream observations; CI does not re-download official files.

The [official MSM8960 DTSI](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/arch/arm/boot/dts/qcom/qcom-msm8960.dtsi)
is **not** byte-identical to the 920 fork. The fork removes the PM8921 interrupt
controller and power-key/keypad/RTC subtree and adds an SSBI label. It also removes
USB controller clock/reset/assigned-rate properties and PHY clock/POR reset
properties. The five compared resource fields are unchanged, but those stripped
dependencies must not silently become an EOS configuration. No restoration patch
was applied: baseline behavior stays preserved pending an exact-device review.
The official PM8921 interrupt-parent pin104 corroborates the firmware resource
association; it does not prove the proposed PM01 pin-number encoding.

## Host implementation and measured result

```sh
python3 scripts/eos_resources.py --check-kernel
python3 scripts/lumia.py build --target soc-objects --jobs 4
python3 -m unittest discover -s tests -v
```

The audit passes. The reference-fork SoC DTB has SHA-256
`b246be3a2f0ed834fbde1c727ddc1378b8e0599a995d44a4df8d72c34c74095d`.
Its existing `/memory` unit-address warning is retained and recorded, not suppressed.
It contains upstream generic placeholder memory; it is not an EOS board description.

Four ARM ELF32 little-endian EABI5 objects were freshly rebuilt: QUP I2C, GSBI,
MSM8960 GCC and pinctrl. All exit 0 with no warnings in that scoped compile; their
hashes match the preserved originals from the baseline build. They are compiled
with the reference config, not a validated EOS configuration. All 32 local tests
pass, including eleven new cases protecting shared-address grouping, address width,
resource apertures, static memory/pointer handling, legacy GICC bounds and unreviewed Linux assignments. Exact hashes/config/logs are
in [evidence](../evidence/2026-10-25-eos-resources.json). CI repeats the audit and
object targets from a fresh setup. No new full-kernel relink is warranted by
these host tooling changes; the previously linked baseline/on/off images remain.

## Static templates are not runtime captures

Additional parent/local bounded parsing reports GIO0 QCOM0500/UID0, PM01
QCOM2038/UID1 dependent on PMIC QCOM2037, and repeated firmware-controller IRQ
resources. The new [static decoder milestone](eos-static-decoders.md) verifies a DALTLMM limit
of 152 pins and operation-specific PMIO GPIO/MPP/IRQ namespaces. **Never globally
subtract 192**. The confirmed standard DSM function1 package identifies pin 51
for an ActiveBoth logic-high override, not a count or Linux physical mapping.

The memory literals are SMEM 0x80000000+0x200000, framebuffer
0x80400000+0x400000, two adjacent SCM0 regions at 0x81400000+0x3d000 and
0x8143d000+0x3000, and RFS0 0x8fb00000+0x300000. BGRT/FPDT pointers have no
established lengths. They are not a complete usable/reserved memory map.
The inventory validator checks known intervals and keeps unsized pointers and
unknown RAM banks distinct; it emits no reserved-memory nodes.

The parent/local task found two enabled **40-byte legacy GICC** records, parking
protocol1 and parked addresses 0x80301000/0x80302000; MADT distributor and legacy
header addresses correlate with Linux's GIC register windows. FADT ARM flags0
do not advertise PSCI. The template tables have zero checksum fields and nonzero
sums. AcpiPlatform recomputes checksum byte 9 before installation and adjusts a
TPM2 control area; general AML fixups and installed runtime values remain unproven. Do not reuse either a PSCI or the reference
DTSI's KPSS CPU enable method without a reviewed handoff case.

Modern iasl rendered later GICC fields beyond the legacy record's length before
warning, causing overlap with adjacent records. The local task rejected those
values through independent bounded parsing. The new original
[`acpi_legacy.py`](../scripts/acpi_legacy.py) implements an explicitly limited
40-byte GICC / 24-byte GICD reader, rejects unsupported/truncated records and
requires an explicit static-template mode to report invalid checksums. It never
fixes or executes tables. Synthetic adjacent-record tests prove that later
virtual-GIC fields are not read or synthesized. This cloud has not run this
parser on the private EOS bytes; its actual-table findings remain attributed to
the local task. Once the table is privately present, the command is:

```sh
python3 scripts/acpi_legacy.py --template .work/research/private/APIC-template.bin
```

Camera resource declarations now identify CAMP/CAMS/CAMF/VFE0 regions, raw IRQs,
clock tuples and GPIO resources. They do not identify sensor silicon, I2C register
protocols or CSI lane maps. The pinned Linux CAMSS match table lists MSM8916,
MSM8996, SDM660, SDM845 and SM8250, with no MSM8960 entry. Neither module codenames
nor those Windows declarations supply a PureView Linux/Android stack.

## Updated static investigation

The [decoder milestone](eos-static-decoders.md) supersedes the previous missing
PMIO schema, DSM GUID, stock touch configuration and absence of firmware selector
logic. Actual product.dat/table selection, panel caller precedence, PEP units and
shared-data consumers remain unresolved. Its targeted Mini questions take priority;
no new upload or physical test is requested. Runtime EFI memory/GOP and CPU
handoff remain separate needs, followed by Android HAL/camera/modem dependencies.
