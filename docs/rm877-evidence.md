# RM-877 exact-image evidence milestone

Review date: 2026-10-25. Original factual findings from authorized Mini static
inspection. Raw FFUs, driver/UEFI files and disassembly stay private. This cloud
validates the attributed record and host tools; it has not acquired or independently
hashed the target firmware. No device or firmware code was executed.

## Verified input, limited trust

| Field | Reported target finding |
| --- | --- |
| Variant / product | RM-877 / 059T019, AT&T US yellow, variant 3805 |
| Software / OS | 3051.50009.1451.1001 / 8.10.14226.359 |
| Platform | Nokia.MSM8960.P5217_ATT |
| Exact filename | RM877_3051.50009.1451.1_RETAIL_nam_att_205_01_473928_prd_signed.ffu |
| Size | 1,684,013,056 bytes |
| SHA-256 | `26b69b84a0e5e529f8dcb696c43625a040e79fa3ec3e96fc7328a7c9bd6faa97` |
| CRC32 / VPL | `7346f0cb`, matching VPL |
| Internal integrity | All 12,844 embedded chunk hashes, GPT and header checks pass |
| Vendor signature trust | Unverified; internal consistency is not vendor authentication |

The filename's 1451.1 and the software metadata's 1451.1001 are recorded as
reported; neither is silently rewritten. Firmware identity does not identify an
attached physical handset or establish runtime table/panel selection.

## What carries across this exact pair

The reference is RM-876 / 059T3B3, SHA-256
`200c402351e7b488fd320bc944a7ab8f1dde2522eac5e7c203584852f541ef08`.
[The comparison record](../rm877-comparison.json) applies only to these two FFUs.

| Compared material | Actual reported relation | Allowed conclusion |
| --- | --- | --- |
| Twelve PLAT ACPI files, including DSDT/2SDT/SSDT | Byte-identical | The selected static resource/template facts also describe this exact RM-877 stock input. Installed tables remain unobserved. |
| External PTANYA.XML | Byte-identical | Same file content, not evidence of the physical panel or its selection. |
| PEP data: 35 devices / 418 action groups / 72 clock names | Byte-identical | The recorded raw actions/data carry to this target input. This does not measure aggregate rails. |
| CONFIG.PCN | Adds _ATT at target offsets 21..24 only | A recorded difference; no behavioral meaning inferred. |
| Fourteen selected UEFI modules | Thirteen differ; PmicDxe identical | Matching tables cannot establish behavior of changed modules. Direct target review is required. |
| PMIC GPIO driver | Whole file identical | The existing static PMIO decoder is corroborated for this exact target; Linux bindings and physical pin behavior remain unverified. |
| PEP driver | Whole file differs, every declared raw PE section matches | Corroborates the static decoder. This is not whole-file equality or general firmware equivalence. |
| Touch driver | Executable sections match; rdata/pdata differ | Code comparison does not carry changed configuration/constants. Package version changes from 4070.57 to 4071.17 under 3051.50009. Direct target registry comparison finds only package identity/path/version differences; selected HID/service/vendor/product selectors, write flags and compared power settings are unchanged. No blanket data or fitted-silicon equality follows. |

The private comparison handoff did not supply individual table hashes or the
target PEP whole-file hash. None is invented. Equality reports are attributed to
the Mini, and the inventory retains the original RM-876 provenance plus explicit
RM-877 corroboration rather than relabeling the old source.

## Changed firmware: directly reviewed target findings

Target AcpiPlatform confirms the reported RM877 TYPE branch and HWIDs
2000/2100/2005/2110 select 2SDT, with DSDT as default. Exact target string bytes
and comparison bounds were not supplied. Actual runtime product.dat was absent
from checked clean locations; DPP was not inspected. No active table selector
is synthesized from missing inputs.

Target ProductCfg directly confirms the same CDPI address/layout mismatch.
Target DisplayDxe confirms panel detection and the low-byte 0xc2 Tanya rule.
Neither finding supplies runtime shared-data state or physical panel identity.
Reference-only caller precedence or general fixups are not assumed for changed
target modules.

Target BOOTARM.EFI SHA-256:
`3e0a832f8d4f8971b31ada5d20b280d1be33d47404f97b367731ee6e21b0b8bc`.
Target winload.efi SHA-256:
`187f21bdd129167cca9e7dd78dd8d60b8733e752a905f7b07d657e56a751b10e`.
The bounded exact-target loader/touch pass is now complete. Winload directly
queries Boolean option 0x16000049 and constructs <configured system root>\system32\acpitabl.dat
using system-root option 0x22000002. A fresh target enumeration found 1,997 stock
System32 entries and no such file. Absence is nonfatal; loaded table length,
bounds and checksum are validated. BCD was not inspected, so actual phone option
and root values are unknown.

Target BOOTARM/winload prefer EFI ACPI2.0 then ACPI1.0 and traverse XSDT/RSDT.
No CDPI patch was observed in the selected paths, not proof of universal absence.
Winload memory-map collection and ExitBootServices retry logic up to four times
are directly traced; no alternative-image acceptance or live calls are inferred.

Target GOP wrappers copy current mode index and 36-byte mode information, but
callers also have preferred-mode logic. Full stock graphics initialization is
therefore not a passive observation route. Actual live mode/base/stride/format
remains uncollected; no observer route is accepted or authorized.

## Host implementation and validation

The original [comparison gate](../scripts/variant_evidence.py) checks the exact
pair, target identity, comparison classes and runtime uncertainty. It validates
record consistency; it does not recompute private firmware hashes.

The original [PE section tool](../scripts/compare_pe_sections.py) reads bounded
ARM PE32 data according to [Microsoft's format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).
It reports whole-file hashes, per-section payload hashes, executable payload
equality and declared layout equality separately. Header/overlay changes cannot
be called whole-file equality; executable equality cannot hide changed data.
It neither loads images nor authenticates them. It also does not claim a complete
loader-validity check. The stricter existing EFI-image checker is unchanged.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/eos_resources.py --check-kernel
python3 scripts/compare_pe_sections.py \
  .work/regression/debug-on/arch/arm/boot/zImage \
  .work/regression/debug-off/arch/arm/boot/zImage
python3 scripts/lumia.py check
git diff --check
```

All 65 tests pass, including eight new synthetic PE/scope/runtime-inference regressions. The new
PE tool also passes on the preserved actual reference-on/off images; those are
its only actual-image inputs here. The unchanged generic-SoC DTB audit passes,
retaining the existing /memory unit-address warning. No kernel patch/image changed
and no full relink was needed. No EOS DTS or boot image is emitted.

## Next dependency: actual handset context

The identified target loader/touch static pass is complete. Remaining specific
observations are runtime-installed tables/CDPI, actual product.dat selection,
panel/fitted touch, aggregate rails, EFI memory/GOP/trust/DT delivery and CPU
parking. Static tracing does not supply those values or approve a collector.

The minimum user help is to establish whether either target handset is already
owned, then its exact normal-mode identity/build and baseline condition. See the
[physical assistance plan](physical-assistance-plan.md). No purchase, live
observer, boot-chain change or flashing is requested. Android still requires a
justified target kernel/device/HAL and PureView case; no validated bootable
RM-877/Android deliverable exists here. The compiled images remain 920 research
artifacts and must not be treated as a handset test proposal.
