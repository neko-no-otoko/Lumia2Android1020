# Physical assistance plan and approval gates

This is a future evidence checklist, not an instruction to unlock or modify a
phone. Ownership of a Lumia 1020 has not been established. No equipment purchase
is proposed. Actual stock FFU board facts are now available; the earlier CAB
acquisition request is superseded. Continue the [handoff source matrix](arm32-handoff.md)
and [board evidence](eos-board-evidence.md) before proposing a handset test.

## Smallest useful help now

No new upload or physical action is requested. The existing Mac Mini task can
continue the [targeted decoder questions](eos-static-decoders.md): remaining PEP policy/mode fields,
panel branch coverage, shared-data layout consumers and stock product.dat
selection/parser bounds. PMIO namespaces and stock touch configuration are now
resolved statically.
This remains private static analysis: no bundled tool or device binary is run,
and no personal Data, DPP, NVI, simlock or provisioning material is processed.
No further work is requested on the MacBook.

The generic upstream ARM32 EFI stub is a reusable licensed source path. The
remaining runtime questions include live EFI memory descriptors, GOP mode/stride,
entry state, executable trust policy and installed CPU/mailbox information.
Normal-mode Info cannot supply all of these. A read-only EFI collector still
requires an approved delivery/execution path; do not treat a boot-chain change
as read-only merely because its payload would only read state.

## If an already-owned target is available later

The intended international target is RM-875, still to verify. Current RM-876
China Unicom firmware is research input only; compare variant evidence before
any target configuration or later exact-device proposal.

Supply only the RM variant (875/876/877), firmware and OS version, and whether it
currently boots stock, charges normally, takes a photo and appears over ordinary
USB. Crop IMEI, serial, product/device identifiers and account details from any
screenshots. State whether an existing Windows host and known-good data cable
are available. These observations establish identity, baseline function and
available tools; they do not require bootloader changes. Do not buy a phone or
switch operating modes for this checklist.

Personal photos/files can be copied through ordinary supported stock interfaces
before experiments. This is user-file backup, not a complete recoverable device
image. Future tool-assisted **read-only Info** would require review of the exact
tool/version, current connection mode and fields to collect. It must not silently
reboot into flash/mass-storage mode, unlock, write or disclose unique IDs. No such
session has been authorized or run here.

## Recovery facts that constrain later decisions

The [WPinternals GettingStarted source](https://github.com/ReneLergner/WPinternals/blob/d270cace796bfe74d1719ba3201bddadb3c508dd/WPinternals/Views/GettingStartedView.xaml),
[Mass Storage source](https://github.com/ReneLergner/WPinternals/blob/d270cace796bfe74d1719ba3201bddadb3c508dd/WPinternals/Views/NokiaMassStorageView.xaml),
[Backup implementation](https://github.com/ReneLergner/WPinternals/blob/d270cace796bfe74d1719ba3201bddadb3c508dd/WPinternals/ViewModels/BackupViewModel.cs),
and [WOA guide](https://github.com/WOA-Project/guides/blob/ce6dd7f8293b1b235bfdd571636e03abea693eb5/WIP-NewGuide.md)
were inspected as original references. WPinternals files carry MIT notices; no
code is imported and no tool from those projects is executed.

- WPinternals raw Backup requires already unlocked Mass Storage. A locked 1020
  cannot be promised a complete pre-unlock raw image using this facility.
- The guide classifies 1020 as Bootloader Spec A. Mass Storage depends on an
  engineering SBL3 with matching OEM/CPU; those are minimum checks, not a blanket
  donor-compatibility guarantee. The tool warns wrong SBL3 may permanently damage
  the phone. This project has not identified or approved any such image.
- Mass Storage does not charge the phone. Windows format prompts must be declined;
  formatting phone partitions can permanently harm the device.
- EFIESP/MainOS/Data backup is distinct from provisioning/DPP and modem-NV
  preservation. A stock OS image is not proof of recovery of unique provisioning.
  DPP damage may require specialist direct-eMMC recovery.
- GettingStarted documents certain Samsung eMMC write-protection failures during
  official/unofficial flashing or OS updates. No conclusion about the target's
  eMMC vendor or susceptibility has been made.

Any later unlock, engineering boot stage, firmware/partition write, mode-changing
experiment or delivery of a custom UEFI program is a separate decision requiring
explicit authorization and an exact-device recovery case. A program that only
reads memory is not operationally read-only if installing/launching it requires
bootloader or partition modifications. No test-point, unlock or flashing commands
are supplied here.

## What runtime evidence might eventually add

Only after legally accessible offline content and reusable source are examined,
identify the precise unresolved facts: firmware-reported usable/reserved memory,
GOP framebuffer address/stride/format, board/revision resource selection and a
reviewed kernel handoff. Collecting these would need an existing trusted access
path or a separately approved later plan. Static ACPI facts alone cannot prove
charging, thermal, eMMC-write or modem safety. A functional PureView photo in the
stock OS provides a baseline, not a Linux sensor/ISP driver or Android HAL.

The next actions are the remaining source questions in the handoff matrix, using
the existing Mac Mini for further local inspection. No device purchase, unlock,
partition write or firmware execution is proposed. Runtime collection must wait
for a concrete exact-device access and recovery decision.
