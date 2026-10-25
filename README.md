# Lumia2Android1020

Experimental research toward Linux and Android bring-up on Nokia Lumia 1020 hardware (EOS / RM-875, RM-876, RM-877).

## Status

Host build foundations are in place: pinned source/license and dependency inventories,
rootless setup, synthetic safety tests, and successful Lumia **920** reference
DTB, driver and full-kernel cross-compilation. A separate pristine upstream
ARM32 kernel now boots a QEMU virt guest and passes eight userspace smoke groups;
this is generic Linux coverage, not a phone or Android framework boot.
The RM-877 target FFU is verified by private Mini static inspection. Selected
ACPI/PEP assets match the exact RM-876 reference; changed UEFI/touch data remain
separate, and general board/runtime equivalence is unverified.
No working Lumia 1020 Linux/Android image, PureView camera support, cellular support,
or safe flashing procedure is claimed. No hardware has been flashed or tested by this project.

- [Executed generic ARM32 virtual tests](docs/virtual-validation.md)
- [Tested / untested / blocked matrix](docs/status.md)
- [Reproduce the host builds and inspect debugging notes](docs/build.md)
- [Source provenance and license review](docs/sources.md)
- [Reviewed build evidence](evidence/)
- [Next source-level work and EOS evidence gaps](docs/next-eos-work.md)
- [Offline EOS data investigation](docs/eos-offline-research.md)
- [Actual EOS board facts and Linux resource audit](docs/eos-board-evidence.md)
- [Verified RM-877 input and scoped comparison](docs/rm877-evidence.md)
- [Stock EOS decoder facts and host checks](docs/eos-static-decoders.md)
- [ARM32 EFI handoff contract and remaining observations](docs/arm32-handoff.md)
- [Staged assistance plan and recovery limits](docs/physical-assistance-plan.md)

Quick start on x86_64 Linux (Python 3.12+, native GCC/Make/curl/dpkg-deb; 8 GiB free):

```sh
python3 -m unittest discover -s tests -v
python3 scripts/lumia.py check
python3 scripts/lumia.py setup
python3 scripts/lumia.py fetch
python3 scripts/lumia.py build --target dtbs --jobs 4
python3 scripts/lumia.py build --target objects --jobs 4
```

All downloads and build outputs remain in ignored `.work/`. The commands compile
the pinned 920 baseline; they do not produce or install an EOS image. Current
full-AOSP storage/RAM needs exceed this cloud allocation, and EOS device/HAL
dependencies remain unverified. No Android release has been selected.

## Initial milestones

1. Audit device-specific source availability, provenance, and licenses.
2. Pin a compatible source baseline and establish reproducible build prerequisites.
3. Add host-side validation and compile checks with saved logs.
4. Debug reproducible failures in small, reviewed changes.
5. Require exact-device validation and a recovery plan before hardware testing.

Virtual tests cannot validate the handset's camera, modem, power management, or boot safety. A Lumia 950 image is not a compatible Lumia 1020 image.

## Research leads

- https://github.com/UEFI-code/LumiaToy
- https://github.com/UEFI-code/linux-6.6-lumia920
- https://github.com/Mainline4Lumia
- https://github.com/Android4Lumia
- https://github.com/Android4Lumia950

These are research references, not endorsed binaries or permission to redistribute third-party software. The Lumia 920 work needs board-specific adaptation; chipset similarity is not device support. Third-party license restrictions must be checked before reuse. Proprietary firmware, credentials, device identifiers and private data must not be committed.
