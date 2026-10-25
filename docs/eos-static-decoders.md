# EOS static decoder milestone

Review date: 2026-10-25. Original factual analysis from authorized Mac Mini static
inspection of the same RM-876 stock FFU; no firmware, AML or driver execution.
Raw binaries and disassembly remain private. Cloud tooling implements independently
written arithmetic checks of the reported facts, not copied vendor routines.

## Provenance

FFU SHA-256: `200c402351e7b488fd320bc944a7ab8f1dde2522eac5e7c203584852f541ef08`.
This is build 3051.50009.1424.0004, RM-876 / 059T3B3. Internal FFU chunk, GPT and
VPL consistency checks pass; the vendor trust chain remains unverified.

| Privately inspected stock file | Bytes | SHA-256 |
| --- | ---: | --- |
| qcpmicgpio8960.sys | 107008 | `6b21dc1c1bd884cd95751140c7db5c5526a1e613f6fb9609cfd26ac14362892c` |
| SynapticsTouch.sys | 507392 | `2b3907b0402783ce18ba1048f2efbf7504e86387a3cc346e32ed99fdafb82b5a` |

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
| Embedded DisplayDxe dispatcher matches Tanya when ID low byte is 0xc2; other ID bits are ignored. Platform value 5 obtains an ID through three DSI reads. | AML DPID 0x00fe00c2 would match **if passed there**. GetPanelConfig also has external XML fallback, low-byte matching and first-record fallback; caller precedence and physical panel remain unresolved. Jessica content in PTANYA.XML is not physical identification. |
| ProductCfgDxe writes shared data at 0x84600000, with product/panel offsets +4/+8; raw SSDT CDPI is 0x015ff000 with byte offsets +2/+6. | Both address and layout differ. Runtime fixup or alternate consumer chain is unresolved. No address/layout patch is justified. |
| PEP parsing validates 35 device packages, 418 action groups and 72 clock names. Display votes SMPS4 then LVS4; off reverses order. Touch shares both rails, also LDO9 and GPIO50. | Numeric levels 1800000/2850000 and loads 40000/20000 retain raw units. CLOCK opcodes 1/2/3/5/7/8/9/10/11, flags, units and shared-vote semantics remain unresolved. No regulator sequence is generated. |
| Synaptics3400_EOS binds NOKIA_TOUCH, configured vendors 3/8 and products PLG0150-01/-02, with F01/F11/F51/F54 labels. | Stock intended configuration is stronger evidence than generic HID/address or aftermarket F12 metadata. It is not an observed silicon model or live function table, and no Linux compatible is assigned. |

## Reproduce host checks

```sh
python3 scripts/firmware_facts.py
python3 scripts/eos_resources.py --check-kernel
python3 -m unittest discover -s tests -v
python3 scripts/lumia.py check
git diff --check
```

All pass: 45 tests, including eight new namespace, bitfield, boundary and inference
regressions. The generic-SoC DTB remains unchanged. Its existing /memory
unit-address warning is recorded. No kernel patches or images changed, so the
preserved baseline/reference-on/off links remain the relevant compile evidence.
No EOS board is enabled; host checks do not establish boot, touch or power safety.

## Targeted remaining Mini questions

1. Trace PEP consumers to establish opcode/flag meanings, numeric units, shared
   vote/refcount behavior and suspend/off ordering. Record exact module hashes.
2. Trace panel callers: which source supplies the embedded dispatcher ID, and
   when do external GetPanelConfig records take precedence? Keep runtime DSI
   detection distinct from template DPID.
3. Trace consumers of 0x84600000 versus CDPI 0x015ff000, version/layout handling
   and any bounded ACPI operation-region fixup. Do not patch the mismatch.
4. If present in the **stock image**, inspect only product.dat TYPE/HWID and
   parser bounds/length handling. Do not seek handset provisioning/DPP/NV or
   assume empty/prefix values imply a rigorously exact selector.

These are further private static-source questions, not a user upload or hardware
request. Runtime EFI memory/GOP, permitted DT delivery, CPU parking semantics,
and actual peripheral identity/state remain separate external observations.
Android kernel/device/HAL and PureView dependencies remain unresolved.
