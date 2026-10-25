# Generic ARM32 virtual validation

Review date: 2026-10-25. No handset is available. This pass executes an original
Linux/userspace test suite on QEMU's generic virtual machine. It does not execute
the Lumia reference kernels, private firmware, Android framework or either phone's
drivers. RM-877 remains the 1020 target; RM-937/1520 remains separate.

## What actually ran

QEMU 10.0.13, `virt-10.0,highmem=off,gic-version=2`, Cortex-A15, two CPUs,
256 MiB guest RAM and software TCG. No KVM, guest network, host disk backend,
monitor, external firmware or graphics device is used. Root storage is an
initramfs; writable test files are in guest RAM.

The kernel is pristine official Linux v6.6 at
`ffc253263a1375a65fa6c9f62a893e9767fbebfa`, independently downloaded and pinned.
It uses a separate minimal configuration, source and output directory. None of
the 920 fork's debug mappings or init-finalization modifications is inherited.
The original static ARM32 PID1 program uses pinned Debian glibc and Linux UAPI
headers. No third-party runtime image or handset data is packaged into the guest.

| Executed group | Concrete check | Coverage limit |
| --- | --- | --- |
| Identity | Linux 6.6.0, ARMv7, 32-bit pointers, PID1 | Generic Cortex-A15, not Qualcomm Krait identification |
| Mounts | proc/sysfs/devtmpfs and tmpfs; create/write/read/unlink | No real storage, partitions or eMMC controller |
| Memory | Zeroed anonymous pages; mprotect; child write faults with SIGSEGV | Guest virtual-memory behavior, not phone RAM/reservations or secure memory |
| Fork/pipe | Child message and parent copy-on-write isolation | Generic Linux process/IPC behavior |
| SMP | Pin userspace to CPU1 and restore affinity | QEMU PSCI-backed secondary startup, not Lumia CPU parking/TrustZone |
| Clock/epoll | Timer events through both time32 and time64 syscalls | Generic ARM timer/interrupts, not phone clocks or power |
| Namespace | Child UTS namespace/hostname does not change parent | Root-driven isolation only, not Android app sandbox or SELinux policy |
| Binder ABI | binderfs device creation; protocol 8; mmap; rejected bad pointers/commands | ARM32 kernel/userspace Binder ABI only; no service-manager transaction, framework or HAL |

All eight groups pass, followed by orderly poweroff and QEMU exit 0. A second boot
with missing `/init` deliberately reaches VFS root-mount panic; QEMU still exits0
because reboot is disabled. The harness correctly rejects it. Boot text or exit 0
alone cannot count as success. Partial/duplicate assertions and timeouts also fail.

## Reproduced failures and scoped corrections

The first boot reached PID1 and passed six groups but failed two; its log and
artifacts are preserved privately under `.work/emulation/first-failure/`.

- `timerfd_settime` returned ENOSYS because the minimal configuration omitted
  `CONFIG_COMPAT_32BIT_TIME`. The pinned ARM glibc's default time32 interface
  needs it. Enabling that generic prerequisite fixes the failure; the test now
  checks time64 explicitly too.
- The test expected EFAULT for a null BINDER_VERSION pointer. The inspected
  upstream Linux 6.6 handler deliberately maps failed put_user to EINVAL. The
  assertion was corrected. BINDER_WRITE_READ separately verifies EFAULT for an
  invalid buffer and EINVAL for an invalid command. No kernel behavior was changed.

Requested fragment settings are checked against effective Kconfig after dependency
resolution, so a silently dropped prerequisite fails before compilation. There
are 71 host tests, including six new harness/configuration regressions. These are
separate from the eight guest groups and the bad-boot control.

The final compile emitted no compiler warnings. The minimal guest reports that
strict kernel memory protection is not configured and emits virtual CPU Spectre
mitigation diagnostics. This profile is a test fixture, not a production/security
configuration or an Android-ready kernel configuration.

## Reproduce

```sh
python3 scripts/lumia.py setup
python3 scripts/virtual_smoke.py setup
python3 scripts/virtual_smoke.py machines
python3 scripts/virtual_smoke.py build
python3 scripts/virtual_smoke.py run
python3 -m unittest discover -s tests -v
python3 scripts/lumia.py check
```

The dedicated virtual CI job repeats setup/build/both boots without hardware or KVM.
Exact commands, hashes, failure history and limits are in
[the evidence report](../evidence/2026-10-25-virtual-smoke.json).

[emulation.lock.json](../emulation.lock.json) pins the official source archive and
91 Debian package entries, about 40.7 MB of additional package downloads. Their
full dependency closure includes unused package-management/account-tool files;
only local extraction occurs, with no installation scripts or accounts created.
QEMU uses its pinned native loader/libraries rather than host-library fallbacks.
Every package copyright notice is retained and fingerprinted. QEMU's overall
notice is GPL2; glibc is LGPL2.1+; kernel/UAPI notices include Linux-syscall-note.
No binary guest or third-party payload is committed or released. Allow 4 GiB free
for fresh setup/build; this run left about 24 GiB free of the 32 GiB cloud disk.

## What QEMU can and cannot represent

QEMU documents `virt` as a generic virtual platform, with versioned machine models
and Cortex-A15 ARM32 support. The installed machine list also includes
Versatile Express; no Lumia/MSM8960/MSM8974/Krait machine is listed. Qualcomm-named
BMC models are different hardware. A generic successful boot therefore cannot
validate RM-877 or RM-937. See the [official virt documentation](https://www.qemu.org/docs/master/system/arm/virt.html).

Versatile Express models a development board with different UART/storage/display
devices and some explicitly unimplemented peripherals. It provides another
generic Linux target, not missing Lumia hardware. We did not duplicate this pass
on it merely to increase counts. See [QEMU's board description](https://www.qemu.org/docs/master/system/arm/vexpress.html).

Direct QEMU `-kernel` startup bypasses the phone's EFI entry, Secure Boot,
ExitBootServices, GOP and parking protocol. No modem, camera/ISP/calibration,
charging, thermal, real storage integrity, panel or PMIC safety result follows.
Synthetic software tests cannot identify physical wiring or replace a compatible
driver/HAL stack.

## Android emulation and resource boundary

This is not Android userspace. Binder ABI coverage supplies one useful interface
check but does not establish Android services, application compatibility or a
phone product/release choice.

Full current AOSP source builds require an x86-64 Linux builder with at least
400 GB free disk and 64 GB RAM. This cloud has 16 GiB RAM and about 24 GiB free,
so no full tree was fetched. These are build requirements, not a claim that
running prebuilt Android needs 400 GB. See [official AOSP requirements](https://source.android.com/docs/setup/start/requirements).

Prebuilt Cuttlefish avoids a full source build, but its documented setup requires
KVM and host integration. `/dev/kvm` is absent here. A credible follow-up needs
a Linux host exposing usable KVM/nested virtualization plus a matching pinned
Cuttlefish image and host package; source compilation additionally needs the
400 GB/64 GB floors. No prebuilt image was selected/downloaded, so its compressed
and unpacked disk size is not invented. That path would test a virtual Android
product, not these ARMv7 phones. See [official Cuttlefish setup](https://source.android.com/docs/devices/cuttlefish/get-started).

No handset purchase is needed for more generic software tests. Actual target
runtime observations and device/HAL validation remain unavailable without a
handset and a separately reviewed safe access route. No collector, unlock or
flashing action is proposed by this virtual pass.
