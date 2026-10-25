# Host build guide

These commands only compile the pinned Lumia **920** reference. They produce no
Lumia 1020 image. There are no deployment or device-write commands in this project.

## Prerequisites

Validated host: Debian 13 x86_64, glibc 2.41, Python 3.12.14, native GCC 14.2,
GNU Make 4.4.1, curl 8.14.1, Git 2.52 and dpkg-deb. Python 3.12 or newer is required
for safe tar extraction. The Debian binary tools require glibc 2.38 or newer.
CI also tests Ubuntu 24.04; consult its actual run status before assuming it passes.
Native compiler headers, zlib/OpenSSL development files and common system runtime
libraries are supplied by the host. This is a pinned dependency setup, not a fully
hermetic host image or a guarantee of identical binaries across different hosts.

Allow at least 8 GiB free disk before source extraction/full kernel compilation.
The kernel archive is about 220 MiB compressed and about 1.6 GiB extracted. Tools
add about 136 MiB plus about 40 MiB cached packages. The saved defconfig enables
many other ARM boards, so full compilation costs more than the focused checks.
Use 1–4 jobs; this cloud allocation has 4 effective CPU cores and 16 GiB RAM.

## Reproduce

Run from the repository root:

```sh
python3 scripts/lumia.py inventory
python3 -m unittest discover -s tests -v
python3 scripts/lumia.py check
python3 scripts/lumia.py setup
python3 scripts/lumia.py fetch
python3 scripts/lumia.py build --target dtbs --jobs 4
python3 scripts/lumia.py build --target objects --jobs 4
python3 scripts/lumia.py build --target kernel --jobs 4
```

`setup` downloads only the 22 hashed Debian packages in `dependencies.lock.json`
and unpacks them into `.work/tools`. It needs no root access and executes no
package maintainer scripts. If a pinned pool URL is retired, stop and review a
new package/hash set; do not silently fall back to floating versions.

`fetch` accepts only the reviewed kernel archive, checks SHA-256, and extracts
with Python's data filter, rejecting traversal and special files. Source-contained
symlinks are necessary for the kernel's include paths; escaping links are rejected.
The archive receipt identifies the original extraction. It does **not** attest
that a subsequently edited source directory is pristine. Preserve local edits;
for a fresh extraction move that directory aside before rerunning `fetch`.

The build uses the upstream `lumia920_defconfig` without Android configuration
changes. The driver targets are `drivers/video/fbdev/lumiafb.o` and
`drivers/mmc/host/easy_mmc.o`. The full target is `zImage`; it does not build a
complete modules set, rootfs, UEFI loader, Android boot image or installable OS.

Every build writes a raw log and JSON report to `.work/logs/`, with exact make
arguments, return code and successful artifact hashes. Reports are ignored by
Git until manually reviewed and summarized in `evidence/`.

The equivalent make invocation, after preparing the environment, is:

```sh
export PATH="$PWD/.work/tools/usr/bin:$PATH"
export LD_LIBRARY_PATH="$PWD/.work/tools/usr/lib/x86_64-linux-gnu"
export BISON_PKGDATADIR="$PWD/.work/tools/usr/share/bison"
export M4="$PWD/.work/tools/usr/bin/m4"
export KBUILD_BUILD_USER=eos-builder KBUILD_BUILD_HOST=cloud-build
export KBUILD_BUILD_TIMESTAMP='2026-08-11 07:21:00 +0000'
export KBUILD_BUILD_VERSION=1 LC_ALL=C TZ=UTC
make -C .work/sources/linux-lumia920 O="$PWD/.work/build/linux-lumia920" \
    ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- lumia920_defconfig
make -C .work/sources/linux-lumia920 O="$PWD/.work/build/linux-lumia920" \
    ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j4 \
    qcom/lumia920.dtb qcom/lumia920-simple.dtb
```

## Host debugging already resolved

The snapshot.debian.org index request received HTTP 403 from the environment's
network proxy. Signed Debian trixie indexes from deb.debian.org succeeded; all
downloaded binaries were checked against their Packages SHA-256 fields and then
locked. No repository authentication or new credentials were needed.

A rootless download-only apt attempt initially tried to lock the system dpkg
database. Dependency discovery was corrected to use a workspace-local status
copy and cache; the checked-in setup bypasses apt and uses the resulting exact
package URLs and hashes. Nothing was installed into system directories.

Relocated Bison first failed with `m4 subprocess failed: No such file or directory`.
Setting both `M4` and `BISON_PKGDATADIR` fixed its data/executable paths. The next
configuration failed with `unknown assembler invoked`: the relocated ARM binutils
could not locate `libbfd-2.44-armhf.so`. The local library path resolves that.
Configuration and focused cross-compilation then completed successfully.

The tiny DTB emits CPU `reg_format` / default address-size warnings because its
`cpus` node omits address/size cell declarations. They remain visible; a successful
DTB compile is not device-tree binding validation. No warnings were suppressed.

## Android resource gate

```sh
python3 scripts/lumia.py android
```

This deliberately exits 2 with the missing dependencies. Current
[AOSP workstation guidance](https://source.android.com/docs/setup/start/requirements)
calls for an x86_64 Linux workstation, 400 GB free disk and 64 GB RAM. Against the
initial cloud inventory, that is about 370 GB more free storage and 48 GiB more
RAM. These are current AOSP planning numbers, not a selected EOS Android release.
An older release needs its own justified kernel/HAL/toolchain/resource assessment.

This session stays on the cloud environment. Moving to a Mac Mini requires an
inventory and a supported Linux build plan, and would not supply missing EOS
drivers. No MacBook is part of this workflow.
