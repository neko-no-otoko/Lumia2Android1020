# EOS static decoder milestone

Review date: 2026-10-25. Original factual analysis from authorized Mac Mini static
inspection of the same RM-876 stock FFU; no firmware, AML or driver execution.
Raw binaries and disassembly remain private. Cloud tooling implements independently
written arithmetic checks of the reported facts, not copied vendor routines.

The current user-selected target firmware is verified **RM-877 /059T019**. Actual
handset identity/state remains unobserved. The analysis below originated from
**RM-876**; its limited target corroboration is recorded separately.
Shared EOS names do not prove board equivalence. A provenance-backed variant
comparison is required before emitting any RM-877 target configuration. The new
[exact-image comparison](rm877-evidence.md) now corroborates the selected shared
tables and PMIC/PEP decoder scope; changed touch data and UEFI stay separate.
No cross-flash or hardware action is proposed.

## Provenance

FFU SHA-256: `200c402351e7b488fd320bc944a7ab8f1dde2522eac5e7c203584852f541ef08`.
This is build 3051.50009.1424.0004, RM-876 / 059T3B3. Internal FFU chunk, GPT and
VPL consistency checks pass; the vendor trust chain remains unverified.

| Privately inspected stock file | Bytes | SHA-256 |
| --- | ---: | --- |
| qcpmicgpio8960.sys | 107008 | `6b21dc1c1bd884cd95751140c7db5c5526a1e613f6fb9609cfd26ac14362892c` |
| SynapticsTouch.sys | 507392 | `2b3907b0402783ce18ba1048f2efbf7504e86387a3cc346e32ed99fdafb82b5a` |
| QCpep8960.sys | 900896 | `f1ce114dab7a543b92e14d4ed5361127ba220440ec754f1403c92a2bf90a9642` |

Hashes of the other inspected UEFI modules were not supplied with the factual
handoff. Their findings are attributed to that local analysis of this FFU, not
represented as independent cloud byte-level verification. No third-party code
or license grant is inferred from these files; none is imported or redistributed.

## Resolved static facts and limits

| Finding | Consequence and remaining limit |
| --- | --- |
| PMIO has 17 arguments. Named indices are recorded in eos-resources.json; unused indices remain uninterpreted. GPIO I/O slots 192..235 map to Windows indices 0..43; MPP slots 128..139 to 0..11. IRQs independently span 0..255. | Display I/O slot 234 gives Windows GPIO index 42. IRQ 51 must not subtract 192. Neither is automatically a Linux GPIO binding. |
| PM01 DSM GUID matches the standard GPIO GUID; function 0 returns Buffer{3}, function 1 Package{51}; Arg1/Arg3 are not inspected. | Pin 51 has the documented controller-relative ActiveBoth logic-high override. It is not a count or physical-pin assignment. See [Microsoft's definition](https://learn.microsoft.com/en-us/windows-hardware/drivers/bringup/gpio-controller-device-specific-method---dsm-). |
| DALTLMM rejects pin indices 152 and above; config registers start at 0x00801000 with stride 0x10, I/O at +4. Bit 29 chooses packed format. | Pure decoding covers both field layouts. New-format drive is four bits; its top bit can overlap writer direction bit 9, while readback drive is three bits. This ambiguity is retained without masking, repairing or inferring electrical settings. Output nibbles 2/3 mean clear/set; other values stay unspecified. |
| AcpiPlatform reads fs0:\Nokia\product.dat, comparing TYPE with RM-877 and HWID with 2000/2100/2005/2110; matching branch selects 2SDT, default DSDT. | Comparisons use parsed value length, so this is not a proven exact-match parser. Actual product.dat is absent. No active table selector is implemented. The loader recomputes checksum byte 9 and adjusts a TPM2 control area; general AML fixups remain unproven. |
| Embedded DisplayDxe dispatcher matches Tanya when ID low byte is 0xc2; other ID bits are ignored. Platform value 5 obtains an ID through three DSI reads. | AML DPID 0x00fe00c2 would match **if passed there**. The traced operation0/platform5 branch calls GetProductInfo, performs three DSI reads and uses compiled XML; it does not call GetPanelConfig. That is a bounded branch result, not universal precedence or physical identification. Jessica content in PTANYA.XML is not physical identification. |
| ProductCfgDxe writes shared data at 0x84600000, with product/panel offsets +4/+8; raw SSDT CDPI is 0x015ff000 with byte offsets +2/+6. | Both address and layout differ. Runtime fixup or alternate consumer chain is unresolved. No address/layout patch is justified. |
| PEP parsing validates 35 device packages, 418 action groups and 72 clock names. Display D0 votes SMPS4 then LVS4; D3 actions reverse order but retain a voltage vote. Touch shares both rails, also LDO9 and GPIO50. | The final stock consumer pass and pinned upstream RPM layout corroborate field labels and per-client arithmetic below. Physical aggregate rails, EOS routing and runtime effects remain unobserved. No regulator sequence is generated. |
| Synaptics3400_EOS binds NOKIA_TOUCH, configured vendors 3/8 and products PLG0150-01/-02, with F01/F11/F51/F54 labels. | Stock intended configuration is stronger evidence than generic HID/address or aftermarket F12 metadata. It is not an observed silicon model or live function table, and no Linux compatible is assigned. |

## Reproduce host checks

```sh
python3 scripts/firmware_facts.py
python3 scripts/eos_resources.py --check-kernel
python3 -m unittest discover -s tests -v
python3 scripts/lumia.py check
git diff --check
```

All pass: 57 tests. Twelve added cases across the PEP checkpoints cover selector units/policies, closest
ties, unavailable rates, overflow boundaries, tuple order, resource-type lengths,
independent vote sums, clamp/round boundaries, shared CXO votes and variant scope. The generic-SoC DTB remains unchanged. Its existing /memory
unit-address warning is recorded. No kernel patches or images changed, so the
preserved baseline/reference-on/off links remain the relevant compile evidence.
No EOS board is enabled; host checks do not establish boot, touch or power safety.

## PEP consumer findings

The same RM-876 stock QCpep8960 parser/converter/executor establishes:

| CLOCK opcode | Static operation |
| --- | --- |
| 1 / 2 | Enable / disable |
| 3 | Set frequency |
| 4 | Invert with argument 1 |
| 5 | Assert then deassert reset |
| 6 | Select external source |
| 7 | Set divider when nonzero |
| 8 | Enable then set frequency |
| 9 | Configuration-policy API; all ten observed stock tuples select CSI muxes; other values unresolved |
| 10 / 11 | Assert / deassert reset |

Frequency selectors 1..4 use Hz, 5..8 kHz, 9..12 MHz. Within each group the
policies are at least, at most, closest and exact. Closest ties choose lower.
Selector 3 means Hz/closest; it is not an observed runtime clock rate. The pure
host model uses synthetic candidate lists only, and rejects conversion-overflow
cases whose exact machine behavior was not supplied.

The consumer's six-item TLMM tuple is **[pin, output value, function, direction,
pull, drive]**. The host helper names fields in that order and checks their packed
field domains; it emits no register writes or electrical configuration.

PMICVREGVOTE item 2 is a resource **type**, not an enable flag. Types 1/2/7 take
7/10/1 parameters after the type, giving full package lengths 9/12/3. A 60-byte
IOCTL 0x80060fd4 carries per-client votes. For LDO/SMPS types 1/2, the first field
aggregates by maximum; the next two independently sum, round by (sum+500)/1000
and clamp to 1023, with packed widths 23/10/10. Microvolt/microamp units are a
statically corroborated field labels in the final stock consumer/upstream RPM
comparison, rather than measured physical rail values. Remaining routing/source
values stay literal. The host model deliberately rejects unestablished overflow domains.

Type 7 CXO_CLOCK OR-aggregates one-bit client votes. Clearing one client while
another votes on leaves the aggregate on; an aggregate of zero is still not an
observation of the physical oscillator. Shared display/touch rails require voting
semantics rather than independent enable/disable sequences. No Linux regulator
implementation or power sequencing is emitted.

## Final bounded RM-876 static pass

The stock consumer gives LDO fields after name/type as microvolts, peak microamps,
average microamps, force mode, pin-control mask, pin function and pull-down.
SMPS adds power mode, switching-frequency selector and clock-source selector.
LVS type 4 has enable, pull-down, pin-control mask, pin function and optional HPM.
Enable and pull-down are per-client OR votes. Force 2 means auto where supported,
3 high-power in the corroborated three-bit encoding; SMPS power 0 is hysteretic,
and switching selector 6 corresponds to 3.2 MHz. EOS pin routing/source values
remain unresolved. The host LVS model covers only enable/pull-down aggregation.

The final RM-876 snapshots retain these **per-client votes**, not rail readings:

| Client/state | Stock reported vote |
| --- | --- |
| DISP D0 | SMPS4 1.8 V, peak/average 40/20 mA, force 3; LVS4 enable |
| DISP D3 | SMPS4 still 1.8 V, peak/average 100/100 microamps, force 2 |
| TCH1 D0 | SMPS4 1.8 V, 25/25 mA; LDO9 2.85 V, 18/12 mA; LVS4 enable |
| TCH1 D3 | LDO9 remains 2.85 V, 5/5 mA; clears its own LVS4 enable and separate SMPS4 voltage/current vote |

A client clear is not aggregate off. The snapshot inventory records only reported
prefix fields; tests use explicitly synthetic trailing fields for arithmetic and
do not invent missing stock package values.

All ten stock operation-9 tuples concern five CSI pixel/RDI outputs. Their final
argument chooses a mux; preceding generic slots 11/12 do not mean MHz. Selectors
1/2/3 give logical A/B bits 00/10/01, corroborating Linux CSI0/CSI1/CSI2 parents.
RM-876 CAMF requests CSI1 and CAMS CSI0; neither proves sensor silicon or lane maps.

The independent cloud comparison pins official Linux v6.6 commit
[ffc253263a1375a65fa6c9f62a893e9767fbebfa](https://github.com/torvalds/linux/tree/ffc253263a1375a65fa6c9f62a893e9767fbebfa).
[MMCC CSI mux definitions](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/drivers/clk/qcom/mmcc-msm8960.c)
and [RPM8960 regulator masks/modes](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/drivers/regulator/qcom_rpm-regulator.c)
match the pinned reference files byte-for-byte. Their hashes are in the inventory,
and the existing source audit now checks them. Linux current conversion truncates
rather than the stock consumer's rounded sum, so that behavior is not conflated.
No source from these files is imported into a hardware driver.

The ProductCfg GUID occurs only in ProductCfgDxe and DisplayDxe among 14 selected
PEs; that bounded scan is not a universal absence claim. Winload constructs
<configured system root>\system32\acpitabl.dat from option 0x22000002. Its optional
table loader is gated by 0x16000049; no BCD was read or changed. The file was absent
among 1,975 checked stock System32 entries. Generic BOOTARM/winload paths supplied
no observed Nokia CDPI edit. The address/layout mismatch remains unresolved, not
established as a firmware defect.

## Current next dependency: exact-target changed firmware

The [RM-877 input/comparison milestone](rm877-evidence.md) closes the former input
gap: selected ACPI/PEP assets match these exact images, PMIC GPIO is identical,
and PEP raw sections match. Thirteen selected UEFI modules and touch data differ.
The preceding analysis retains its RM-876 provenance; only explicitly corroborated
facts carry to the exact target. The bounded target loader/touch pass is complete.
Runtime tables/CDPI, panel/fitted touch, aggregate rails and EFI state remain
unobserved. Minimum next help is ownership/normal stock identity/condition; no
new upload, live observer or hardware operation is requested.
Android kernel/device/HAL and PureView dependencies remain unresolved.
