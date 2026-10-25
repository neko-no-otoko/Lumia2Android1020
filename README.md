# Lumia2Android1020

Experimental research toward Linux and Android bring-up on Nokia Lumia 1020 hardware (EOS / RM-875, RM-876, RM-877).

## Status

Research bootstrap only. No working Android image, PureView camera support, cellular support, or safe flashing procedure is claimed. No hardware has been flashed or tested by this project.

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
