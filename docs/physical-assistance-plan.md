# Physical assistance plan and approval gates

This is a future evidence checklist, not an instruction to unlock or modify a
phone. Ownership of a Lumia 1020 has not been established. No equipment purchase
is proposed. Actual stock FFU board facts are now available; the earlier CAB
acquisition request is superseded. Continue the [handoff source matrix](arm32-handoff.md)
and [board evidence](eos-board-evidence.md) before proposing a handset test.

## Minimum help needed now

The exact RM-877 FFU is verified, selected shared assets are compared, and the
bounded target loader/touch static pass is complete. No firmware reupload or
further identified local static route is pending. Ownership of either target
handset is still unknown. The next useful information is:

1. Confirm whether an RM-877 Lumia 1020 is already owned/available. The separate
   RM-937/1520 effort needs its own identity; this repository remains 1020-only.
   If no target is available, say so. No purchase is requested.
2. If already owned, report the model/RM, firmware and OS build visible in normal
   stock settings, plus public product SKU only if already visible. Do not open
   the phone, use service modes or inspect provisioning to find missing fields;
   report unknown instead. Omit IMEI, serial, MAC and account details.
3. Report baseline condition: whether it already boots stock, charges normally,
   stock camera works and ordinary USB is recognized. Unknown is acceptable.
   Also state whether a Windows host and known-good data cable are available.
   No tool install, mode change, unlock, flash or observer launch is requested.

These facts establish the actual device/build, baseline function and available
access/recovery context. A matching downloaded FFU does not establish that a
handset is the same variant or safe to modify. Do not cross-flash a different
1020 variant to match the chosen research input.

Personal files may be copied through ordinary supported stock interfaces before
any later experiments. This is user-file backup, not a complete recoverable raw
image. No personal files, accounts, DPP, modem NV or provisioning data should be
sent for this research.

## What this first step cannot supply

Normal settings/Info do not provide runtime EFI memory descriptors, GOP
base/stride/format, installed ACPI/CDPI, CPU/mailbox state, fitted touch/PDT or
aggregate rails. The upstream ARM32 EFI source contract is known, but target
alternative-image acceptance and permitted DT delivery remain unverified.

The target GOP wrappers copy mode information, but their callers also have
preferred-mode logic; full stock graphics initialization is not a passive
collector. No live-observer route has been accepted or authorized. Even a
read-only payload can require a boot-chain write to launch. After the minimal
handset context is available, review a concrete access/recovery proposal before
any such operation. Tool-assisted Info must not silently reboot into another
mode or reveal unique identifiers. No such session is requested here.

Current target static work uses the Mini; no MacBook work is requested.

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

The next action is the minimal ownership/identity/condition report above, not
more speculative board code or a collector launch. Hardware-specific execution
must wait for an exact-device access and recovery decision. The supplied target
FFU and scoped comparison are recorded in [RM-877 evidence](rm877-evidence.md).
