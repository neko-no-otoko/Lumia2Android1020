# Tested, untested and blocked

Review date: 2026-10-25. This is a host build/research foundation, not a Lumia 1020
Linux port or Android distribution. No handset was connected, booted or flashed.

| Area | State | Evidence and limit |
| --- | --- | --- |
| Existing public GitHub repository | Verified | Expected initial main commit `dde83f8d393a75ef7fd37acc8eed56fef31a798c`; work is on a development branch and draft PR. |
| Cloud resources | Tested | Debian 13 x86_64, CPU quota 4 cores, 16 GiB RAM, about 30 GiB initially free. Enough for this kernel work. |
| Dependency setup | Tested | 23 hash-pinned Debian packages, including GNU patch; rootless extraction with no credentials or system installation. |
| Host safety tests | Tested | 37 local tests cover host safety, patch preconditions, static formats and EOS resource interpretation; native synthetic CAB/iasl integration also passes. |
| Lumia 920 tiny DTB | Compiled with warnings | CPU address/size-cell diagnostics remain; not binding-schema or hardware validation. |
| Patched 920 tiny DTB | Compiled without the reproduced warnings | Only two CPU-cell properties added; all 28 nodes and 126 original properties preserved. Baseline retained separately. |
| 920 early-debug isolation | Both full links and paired object regression passed | Full off link found and fixed a panic-path caller; six affected objects now covered per mode. Default-off resolution is checked. Console symbols are absent from off vmlinux. Baseline and init-finalization overrides are retained. |
| Lumia 920 simple DTB | Compiled | No target-specific diagnostics observed; not hardware validation. |
| Lumia 920 framebuffer/eMMC objects | Compiled | ELF32 little-endian ARM EABI5 objects. No device code was executed. |
| Lumia 920 full zImage | Compiled | Exit 0 after about 21 minutes; 8,667,648-byte ARM image. One unused-function warning; see the kernel report for hashes. A zImage alone is not an OS image. |
| GitHub CI | Passed at recorded commit | Fresh Ubuntu 24.04 setup, safety tests, both DTBs and both objects passed; see evidence for run/head. Latest PR checks remain the authority for subsequent commits. |
| EOS stock board facts | Static analysis available | Parent/local FFU extraction and AML disassembly supplied actual RM-876 facts. Cloud independently cross-checks original factual inventory against pinned Linux. Vendor trust and runtime selections unresolved; raw data private. |
| EOS resource audit / SoC driver objects | Passed host checks | Five controller bases/IRQs and four candidate GSBI pinmux groups cross-checked; four ARM objects freshly rebuilt. No Linux board bindings or hardware enablement inferred. |
| EOS kernel / device tree | Blocked | Partial actual RM-876 board facts now recorded; usable/reserved memory, handoff, controller translation and power/selection semantics still unresolved. No EOS DTS emitted. |
| EOS UEFI loader / kernel handoff | Blocked | Upstream GPL ARM32 EFI stub identified and existing PE images checked; actual EOS UEFI services/trust, board DT and parking contract remain unverified. LumiaToy is not imported. |
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

The CPU-cell correction and separate early-debug isolation work are described in
[`next-eos-work.md`](next-eos-work.md). Neither establishes an EOS board port.

Expanded source/data investigation and its exact access blocker are recorded in
[eos-offline-research.md](eos-offline-research.md). The staged
[physical assistance plan](physical-assistance-plan.md) explains what help is
useful now and which later operations require separate authorization.

Actual stock EOS facts and targeted next static questions are now recorded in
[eos-board-evidence.md](eos-board-evidence.md). This supersedes the earlier lack
of board-description input; it does not establish boot or runtime support.

[ARM32 handoff research](arm32-handoff.md) separates the reusable upstream EFI
contract from unresolved EOS static mappings and required runtime observations.
Existing images pass host PE checks; no new image or device test was performed.
