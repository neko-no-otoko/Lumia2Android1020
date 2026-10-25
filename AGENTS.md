# Working agreement

Use development branches and draft pull requests. Never merge or change repository
visibility/permissions. Project code and documentation pushes are authorized.

Keep dependencies pinned with hashes and provenance. Check licenses before reuse;
link restricted references instead of importing them. Do not commit proprietary
firmware, credentials, private data, device identifiers, or raw device dumps.

Cloud-only host builds and synthetic tests are in scope. Hardware flashing,
partition writes, bootloader changes, paid compute, credential creation and
external developer outreach are out of scope. No MacBook substitution.

Report exact commands, exit codes, warnings and artifact hashes. Compilation is
not proof of Lumia 1020 boot, camera, modem, charging, or power safety. Do not
rename Lumia 920/950 trees to suggest EOS support. No Android release selection
until an EOS kernel/device/HAL compatibility case exists.

Run `python3 -m unittest discover -s tests -v` and `python3 scripts/lumia.py check`
before pushing. Keep raw downloads/build logs under `.work/`; only reviewed,
sanitized summaries belong in `evidence/`.
