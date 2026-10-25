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

`setup` downloads only the 23 hashed Debian packages in `dependencies.lock.json`
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

## Reviewed source patches

The original source and full-kernel artifacts are retained. A separate patched
source/output pair is prepared from the same verified archive:

```sh
python3 scripts/lumia.py setup
python3 scripts/lumia.py prepare
python3 scripts/lumia.py build --profile patched --target dtbs --jobs 4
python3 scripts/verify_dtbs.py
```

`patches.lock.json` pins each GPL-2.0-only patch and the before/after hashes of
every changed source file. Preparation checks relative paths, runs a zero-fuzz
dry run, applies the patch, and verifies its output hashes. A receipt supports
appending reviewed patches without silently accepting edited source files.
GNU patch 2.8-2 is the 23rd pinned package (GPL-3+ tool license); its package
copyright notice was reviewed locally. No kernel or loader binaries are imported.

The first patch adds only CPU-node cell metadata. A forced unmodified-DTB rebuild
reproduced its warnings; the patched compile removes them. The focused comparator
checks every original DT node/property byte, allowing only the two new CPU cell
properties, and requires the simple DTB to stay unchanged.

The second patch adds `CONFIG_LUMIA920_EARLY_DEBUG`, default off and explicitly on
in the saved 920 defconfig. It gates the identified early identity mapping, PMD
preservation, console object/calls and EFI/startup color bars together. It does not
restore or change the separate init-memory/read-only finalization overrides.

```sh
python3 scripts/lumia.py prepare
python3 scripts/lumia.py build --target debug-objects --jobs 4
python3 scripts/lumia.py build --profile patched --target debug-objects --jobs 4
python3 scripts/verify_debug.py reference
python3 scripts/lumia.py build --profile patched --debug-mode off --target debug-objects --jobs 4
python3 scripts/verify_debug.py off
python3 scripts/verify_debug.py verify
```

Both patched modes share one output directory; run these commands sequentially.
The baseline uses a separate source and output directory and cannot accept an off
mode. The comparison checks actual ARM object code, allows only source-line
diagnostic changes in the reference mode, and checks removal of the identified
hooks in the off mode. Off is a source-isolation experiment, not an EOS/generic
boot-safety result. Full cloud kernel builds and their measured outcomes are
reported separately; CI runs focused object checks.

For a completed full build, `python3 scripts/verify_debug.py reference --kernel`
or `off --kernel` preserves its linked artifacts only after checking that the
successful build report matches the current config and image hash. The comparator
then also checks linked console inclusion and records both kernel hashes.

At the source-isolation checkpoint, reference-on full compilation exited 0 and
retained an 8,667,648-byte zImage with SHA-256
`6edd1907771994e8670d33ac699ba6cf861f522fb96b1a5d19cd7db181185ffd`.
The original baseline image remains unchanged. The reference-on head, MMU and EFI
stub objects are byte-identical to baseline; setup/init differences are verified
diagnostic line metadata only. Both modes pass the affected-object CI checks.

The subsequent full off-mode link exposed an unconditional panic-console caller
in `kernel/panic.c`. A third pinned patch guards it with the same option and adds
`panic.o` to the affected-object set. Reference-on allocation/code behavior is
preserved; the reference zImage hash stays unchanged. Both full modes now link
with exit 0, and the paired checker confirms console symbols are present only
in reference-on mode. The off zImage SHA-256 is
`a678672622b528e18e37b32d8a43a9d048c0f5f4f310010f629db3d34dbe8e3b`.
These are host tests only. All measured hashes, the reproduced failure and limits are in
[`2026-10-25-debug-isolation.json`](../evidence/2026-10-25-debug-isolation.json).

Relocated Bison first failed with `m4 subprocess failed: No such file or directory`.
Setting both `M4` and `BISON_PKGDATADIR` fixed its data/executable paths. The next
configuration failed with `unknown assembler invoked`: the relocated ARM binutils
could not locate `libbfd-2.44-armhf.so`. The local library path resolves that.
Configuration and focused cross-compilation then completed successfully.

The tiny DTB emits CPU `reg_format` / default address-size warnings because its
`cpus` node omits address/size cell declarations. They remain visible; a successful
DTB compile is not device-tree binding validation. No warnings were suppressed.

## Recorded full-kernel milestone

The existing full build completed on 2026-10-25 at 01:12:49 UTC with exit 0:

```sh
python3 scripts/lumia.py build --target kernel --jobs 4
```

It took about 1,269 seconds on the saved cloud allocation and produced an
8,667,648-byte `zImage` plus a 26,824,116-byte ELF32 little-endian ARM EABI5
`vmlinux`. The source and saved defconfig were not patched for this build. Its only
compiler warning was `init/main.c:1405: mark_readonly defined but not used`,
consistent with the commented-out call already recorded in the source review.
No source workaround or weakened compiler flags were needed.

SHA-256 values, the resolved configuration hash, fixed KBUILD metadata and the
exact make arguments are recorded in
[`2026-10-25-kernel.json`](../evidence/2026-10-25-kernel.json). Both DTB and driver
checks were rerun incrementally after the full build and retained their prior
hashes. The image was inspected as a file; it was not executed, booted or deployed.

Checkpoint commit `516def15fc829808c5fcff1557335968bc5eb47b` passed
[fresh CI run 3](https://github.com/neko-no-otoko/Lumia2Android1020/actions/runs/40149458747),
including all 11 safety tests and focused DTB/driver builds. Full zImage compilation
was performed in this cloud environment, not in CI.

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

## EOS factual resource audit and controller prerequisites

`python3 scripts/eos_resources.py --check-kernel` compiles the unchanged pinned reference-fork
MSM8960 DTSI and cross-checks recorded EOS facts, source hashes, candidate pinmux
groups and clock IDs. It does not emit an EOS DTS. `python3 scripts/lumia.py build
--target soc-objects --jobs 4` compiles QUP I2C, GSBI, MSM8960 GCC and pinctrl
objects under the reference configuration. See [eos-board-evidence.md](eos-board-evidence.md)
for results, diagnostic limits and remaining source questions.
