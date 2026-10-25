# EOS offline investigation

Review date: 2026-10-25. No handset was used. No proprietary firmware bytes were
obtained, executed or published. This work prepares data-only inspection; it has
not recovered any actual EOS board parameters.

## Concrete data dependency

The pinned [RM-875 firmware index](https://github.com/thaihoangduylinh/WPCabLinks/blob/fd913b6e1f683e6ae9c737583da53e386b5294d9/WP-Special-CAB-Links/RM-875_eu_spain_367-Firmware-3051.50009.1451.1004.html)
contains EOS ACPI, EFI product configuration and UEFI package links. Exact URLs
and indexed SHA-1 expectations are in [firmware-references.json](../firmware-references.json).
The original links use HTTP; HTTPS equivalents were also tried. A SHA-1 filename
is a provenance clue and input-match check, not independent signature validation.
A second [RM-877 index](https://github.com/Ritsu909/WP-Special-CAB-Links/blob/7acdd23423d619de421669e8ae91962774619d1a/RM-877_nam_att_205-Firmware-3051.50009.1451.1001)
corroborates the ACPI/UEFI URLs; shared packages do not establish identical wiring
or runtime configuration across RM-875/876/877.

Actual GETs for all three HTTPS URLs returned HTTP 403 in this environment.
ACPI also returned 403 over original HTTP and with explicit network access.
HEAD checks are recorded separately from these actual GET attempts. No package
file was created. Repeating these denied requests or bypassing the environment's
network policy would not advance analysis. The demonstrated blocker is data
acquisition here; global availability and actual package contents remain unknown.

The smallest useful external dependency is legitimate access to these exact
publicly indexed files, or private delivery of them into the ignored analysis
area. No phone, unlock or firmware installation is needed to attempt that route.
Do not upload firmware, decompiled tables, XML dumps or unique identifiers to this
public repository. Redistribution rights have not been established.

## Method and license evidence

| Original source | What was inspected | Limit / reuse decision |
| --- | --- | --- |
| [nokia-fame-mainlining FFU inventory](https://github.com/samcday/nokia-fame-mainlining/blob/d7920b332a8c26a40cc9d998351081796c15c76b/notes/ffu-inventory.md) and [ACPI notes](https://github.com/samcday/nokia-fame-mainlining/blob/d7920b332a8c26a40cc9d998351081796c15c76b/notes/acpi.md) | FFU to PLAT FAT to DSDT/SSDT, followed by static ACPI decompilation and PCFG extraction. | Method reference only; another model/SoC. No source copied or tools from that repository executed. No addresses transferred to EOS. |
| [Mainline4Lumia panel extractor](https://github.com/Mainline4Lumia/LumiaScripts/blob/82da0aa9e9ac4f105cca58eeb16b228d6e222f77/scripts/acpi_panel_extractor.py) | Small fixed-column parser of decompiled static PCFG bytes; MIT LICENSE reviewed. | Read statically, not imported/executed. The original parser here handles literal buffers with size/XML checks and retains every candidate. |
| [glance](https://github.com/Chinmay-KB/glance/tree/6375b47045e3e118cb965eb6d4c3026fb14ec70e) | MIT README/briefing and tree: WP8.1 USB screen mirroring on RM-875. | Does not supply a Linux board tree, Android HAL or kernel handoff. No code imported or executed. |
| Official Debian cabextract, libmspack and ACPICA packages | Native CAB extraction and `iasl -d`; package copyright notices reviewed locally. | Versions, SHA-256 and individual licenses in [research-tools.lock.json](../research-tools.lock.json). Locally unpacked without maintainer scripts; no binaries republished. |

The CAB may contain nested/delta/package-specific data rather than directly
readable AML files. That question cannot be answered without bytes. The current
inspector deliberately recognizes only DSDT/SSDT at file start. An empty table
list would require further reviewed format investigation; it would not establish
that the firmware lacks ACPI or useful board facts. PCFG may have multiple runtime
branches. Panel XML alone cannot establish framebuffer address/stride, usable RAM,
reserved-memory map, a safe loader, or Linux power/storage behavior.

## Reproducible private inspection

On the existing x86_64 Linux host, setup and synthetic verification are:

```sh
python3 scripts/research_tools.py
python3 -m unittest discover -s tests -p test_static_eos.py -v
```

With a lawfully obtained exact input already placed privately under `.work/`:

```sh
python3 scripts/inspect_eos.py acpi-eos .work/research/private/acpi-eos.cab
```

The inspector checks the indexed digest before extraction, bounds CAB sizes,
rejects traversal/spanning/duplicate entries, verifies extracted sizes and table
checksums, and invokes native `iasl -d` with a timeout. It never evaluates AML,
runs device binaries, mounts images, or connects to hardware. Inputs, extraction,
decompiled text and the detailed report remain ignored/private. Review rights
and identifiers before publishing any derived explanation. A digest match still
requires independent provenance/signature review before treating content as
vendor-authenticated evidence.

The native test builds a **synthetic** ASL table, packages it into a synthetic
uncompressed cabinet, extracts it, decompiles it and verifies literal XML bytes.
All five format tests pass locally. They prove tool integration and rejection
cases, not successful extraction of an EOS package. Total local host tests: 21.

## Search coverage and remaining unknowns

Expanded public code/repository searches included `nokia,lumia1020`, `nokia-eos`,
`nokia.acpi.eos`, `RM-875`, `Nokia.MSM8960`, `PCFG EOS`, `dsdt RM-875`, and
`lumia 1020 linux`. No reusable EOS board/kernel/Android HAL chain was verified.
The public repositories of the author of the separate RM-875 pmOS note were
reviewed; that source remains unlocated. No developer was contacted.

Branch lists for Mainline4Lumia/linux and linux-next were inspected, but not all
branch contents. The qcom DTS directory listings in UEFI-code/linux-6.6-lumia920
`master` and `merge_mainline_dts` show 920/generic MSM8960 files, no EOS-named tree.
This is a bounded filename inspection, not proof no relevant code exists.
The public postmarketOS GitLab API request also returned 403 here, so its search
contents were not reviewed. These unresolved searches must not be described as
negative evidence of universal absence.

A legitimate EOS firmware data route is still uninspected because of the access
blocker. Accordingly this project cannot yet conclude physical handset access is
necessary. Android release/HAL/ISP compatibility remains independently unresolved;
Windows camera packages would not become Linux/Android drivers through extraction.
