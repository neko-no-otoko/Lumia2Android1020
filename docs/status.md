# Tested, untested and blocked

Review date: 2026-10-25. This is a host build/research foundation, not a Lumia 1020
Linux port or Android distribution. No handset was connected, booted or flashed.

| Area | State | Evidence and limit |
| --- | --- | --- |
| Existing public GitHub repository | Verified | Expected initial main commit `dde83f8d393a75ef7fd37acc8eed56fef31a798c`; work is on a development branch and draft PR. |
| Cloud resources | Tested | Debian 13 x86_64, CPU quota 4 cores, 16 GiB RAM, about 30 GiB initially free. Enough for this kernel work. |
| Dependency setup | Tested | 22 hash-pinned Debian packages, rootless extraction; no credentials created or system installation. |
| Host safety tests | Tested | 11 synthetic tests for path/archive confinement, hash failure, disk gate, target restrictions, license gate and Android blocker. |
| Lumia 920 tiny DTB | Compiled with warnings | CPU address/size-cell diagnostics remain; not binding-schema or hardware validation. |
| Lumia 920 simple DTB | Compiled | No target-specific diagnostics observed; not hardware validation. |
| Lumia 920 framebuffer/eMMC objects | Compiled | ELF32 little-endian ARM EABI5 objects. No device code was executed. |
| Lumia 920 full zImage | In progress | See the build report for the final outcome. A zImage alone is not an OS image. |
| GitHub CI | Passed at recorded commit | Fresh Ubuntu 24.04 setup, safety tests, both DTBs and both objects passed; see evidence for run/head. Latest PR checks remain the authority for subsequent commits. |
| EOS kernel / device tree | Blocked | No validated EOS board description or source/build provenance chain. The 920 source cannot be relabeled as EOS. |
| EOS UEFI loader / kernel handoff | Blocked | No reviewed reusable EOS handoff implementation. LumiaToy remains reference-only due to its license restriction; no loader was imported or built. |
| EOS Linux boot / USB / SSH | Untested | Upstream 920 claims and separate RM-875 notes do not establish support here. |
| EOS storage integrity / charging / thermals | Untested, blocking hardware work | Needs exact-device source review, memory/power mapping and recovery evidence. No partition writes are authorized. |
| Android product/image build | Blocked | No verified EOS device tree, compatible kernel configuration, full HAL/vendor provenance or justified Android release; cloud also below current full-AOSP resources. |
| Android framework/emulator tests | Not attempted | Would not establish EOS modem, camera, charging or boot safety. |
| PureView camera / ISP / calibration / Android HAL | Blocked | No verified compatible, lawfully reusable Linux/Android stack found. Windows files do not fill this gap. |
| Modem / graphics / audio / sensors | Untested / missing dependencies | No end-to-end EOS driver/HAL evidence. |

## Concrete next dependencies

1. Locate a source-and-license chain for the independently mentioned RM-875 pmOS
   work, or establish an EOS board port from publicly reusable technical evidence.
   Record variant and board-revision differences before assuming RM-875/876/877 parity.
2. Compare EOS memory/reserved ranges, UEFI handoff, panel, GPIO, PMIC/regulators,
   clocks, thermal controls and storage controller against the 920 reference.
   Remove hard-coded 920 assumptions only with evidence; do not invent addresses.
3. Resolve power/clock and storage-safety questions before any future exact-device
   test proposal. Hardware work remains outside this task's authorization.
4. Establish the Android kernel/userspace/HAL ABI case. The saved 920 configuration
   has `CONFIG_ANDROID_BINDER_IPC`, `CONFIG_NAMESPACES` and `CONFIG_SECURITY` disabled.
   Merely enabling them would not supply an EOS Android product or camera stack.
   The source also comments out normal init-memory freeing and read-only marking.
5. Once those dependencies support a specific Android target, budget a suitable
   Linux builder. Current AOSP guidance is 400 GB free disk and 64 GB RAM; the
   present cloud needs roughly 370 GB more free disk and 48 GiB more RAM to meet
   that planning baseline. No move to Mac Mini has been made.

Compile results, exact commands, hashes and debugging notes are in
[`evidence/`](../evidence/) and [`build.md`](build.md). Raw sources, packages,
logs and binaries stay under ignored `.work/`. No binary releases are published.
