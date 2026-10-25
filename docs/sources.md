# Source and license inventory

Review date: 2026-10-25. Exact commit IDs and download policy are in
[`sources.lock.json`](../sources.lock.json). No third-party source or firmware is
vendored. Locally compiled artifacts remain ignored. Existing README content is
retained; no project-wide license has been selected on the owner's behalf.

| Source | Evidence / license review | Decision |
| --- | --- | --- |
| [UEFI-code/linux-6.6-lumia920](https://github.com/UEFI-code/linux-6.6-lumia920/tree/9872e9316212490b7db8e3371fa1d63bd3394cc5) | `COPYING`: GPL version 2 with Linux syscall exception; other per-file licenses apply. `lumiafb.c` and `easy_mmc.c` carry GPL SPDX notices. | Download hash-pinned source locally, compile 920 baseline only. No redistribution of binary images. |
| [UEFI-code/LumiaToy](https://github.com/UEFI-code/LumiaToy/tree/2a256c84102e33a15f0d93e069f1b8b21ad93c3e) | README limits commercial use. A general redistribution grant was not established. | Reference only; do not import loader code, bundled kernel, DTB or initramfs. |
| [petronijus/nexusQ-reloaded](https://github.com/petronijus/nexusQ-reloaded/tree/d310161beb7d145be083fbfae0bc022ac24f8ca7) | Reports GPL-2.0; not audited for reuse. August notes mention a separate RM-875 pmOS device. | Evidence lead only. Nexus Q is OMAP, not EOS. No EOS source located. |
| [Mainline4Lumia/LumiaQuickStart](https://github.com/Mainline4Lumia/LumiaQuickStart/tree/4ecbfb8c93ef8789207f470126825e3ac91090c3) | License not audited. README describes installing a boot shim/developer menu. | Reference only; do not run its installation script. Generic project membership is not EOS support. |
| [Android4Lumia/notes](https://github.com/Android4Lumia/notes/tree/281fbd5ff1e2bf1500921ca69bd888238e552b3d) | License not audited. LOS 14.1 manifest names MSM8x27, fame, glee and zeal sources. | Reference only; no verified EOS Android manifest or tree. Do not fetch proprietary vendor payloads. |
| [Android4Lumia950 talkman](https://github.com/Android4Lumia950/android_device_msft_talkman/tree/085f931c7b2cb5e7c8f21a64f60d753699b83b42) | License not audited. BoardConfig specifies ARM64/ARMv8 and MSM8992. | Incompatible reference; not imported. |
| [Mainline4Lumia talkman](https://github.com/Mainline4Lumia/android_device_msft_talkman/tree/007e905bffa4c178bac27e42ba710005377309b9) | License not audited; different device. | Its Lineage branch is not a reason to select that Android version for EOS. |

The 920 kernel README at the pinned August 11, 2026 revision reports boot,
framebuffer, eMMC, USB networking and SSH, and unresolved RPM/clock power use.
Those are upstream reports; this project has verified host compilation only.
The source hard-codes the 920 framebuffer address and includes a polling eMMC
driver. `init/main.c` also comments out `free_initmem()` and `mark_readonly()`;
the full build reports `mark_readonly` as unused. This baseline bypasses those
normal kernel initialization/hardening steps and is not Android-ready.
Similar silicon does not validate EOS memory regions, panel, regulators,
reserved memory, USB role/power, storage access, modem or camera behavior.

The separate RM-875 claim appears in the
[August 16 Nexus Q analysis](https://github.com/petronijus/nexusQ-reloaded/blob/d310161beb7d145be083fbfae0bc022ac24f8ca7/docs/2026-08-16-idle-700mhz-deep-analysis.md).
That note and later `HANDOVER.md` suggest USB connectivity for another Lumia,
but neither provides an EOS source/build provenance chain. Network addresses in
those notes are irrelevant to this project and are not copied here.

## Device identity and search boundaries

Target: EOS / Lumia 1020, RM-875/RM-876/RM-877 family, MSM8960, ARMv7, 2 GB RAM.
[Nokia's launch specifications](https://blogs.windows.com/devices/2013/07/11/nokia-lumia-1020-the-smartphone-camera-revolution-begins/)
confirm dual-core 1.5 GHz and 2 GB RAM;
[Nokia's later device article](https://blogs.windows.com/devices/2014/04/18/3d-printed-nokia-tech-chocolate/)
explicitly names MSM8960. Qualcomm identifies the
[1020's Snapdragon S4 Plus](https://www.qualcomm.com/news/onq/2013/07/41-million-reasons-get-excited-about-nokia-lumia-1020)
and lists [MSM8960 in the S4 Plus family](https://www.qualcomm.com/processors/products/s4-s1).
Exact variant wiring and board revision remain unverified here. This is a 32-bit
platform; Lumia 950 ARM64 trees and images cannot substitute for it.

Public GitHub repository searches on the review date included `lumia1020`,
`"lumia 1020"`, `"rm-875"`, `android_device_nokia_eos`, `linux nokia eos`, and
`user:petronijus lumia`; organization repository lists for Mainline4Lumia,
Android4Lumia and Android4Lumia950 were inspected. Targeted code searches covered
`RM-875` in nexusQ-reloaded and `1020` in Mainline4Lumia/linux and Android4Lumia/notes.
No verified EOS Android device tree, compatible full HAL bundle, or PureView Linux
camera stack was located in this bounded search. That is not proof that none
exists publicly or privately. No external developer was contacted.

Windows EOS camera binaries are not Linux sensor drivers, an Android camera HAL,
or a redistributable ISP/calibration stack. They were not downloaded or committed.

## Build tool provenance

`dependencies.lock.json` pins 22 official Debian binary package URLs, versions,
architectures and SHA-256 values discovered from signed trixie metadata. These
are build tools, not handset firmware. Their package copyright notices remain
under `.work/tools/usr/share/doc/*/copyright`; GPL-family compiler/binutils tools,
Bison, Flex, m4, dtc, libc and libelf retain their individual terms and exceptions.
No claim is made that all packages have one license. The binaries are downloaded
for local use, not republished in this repository. Recheck source-offer and
license obligations before any future redistribution.

CI pins `actions/checkout` at `11d5960a326750d5838078e36cf38b85af677262` (v4).
Its MIT `LICENSE` was reviewed at that commit; it runs only on the host CI runner.
