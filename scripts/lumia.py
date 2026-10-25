#!/usr/bin/env python3
"""Pinned host-only Lumia research builds. No device operations are implemented."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
GIB = 1024 ** 3
TARGETS = {
    "dtbs": ["qcom/lumia920.dtb", "qcom/lumia920-simple.dtb"],
    "objects": ["drivers/video/fbdev/lumiafb.o", "drivers/mmc/host/easy_mmc.o"],
    "kernel": ["zImage"],
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def confined(root, path):
    root, path = Path(root).resolve(), Path(path).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"Output must be strictly inside {root}")
    return path


def workpath(name):
    return confined(ROOT, ROOT / ".work" / name)


def require_space(path, gib):
    if shutil.disk_usage(path).free < gib * GIB:
        raise ValueError(f"Need at least {gib} GiB free before this step")


def load_json(name):
    return json.loads((ROOT / name).read_text())


def validate_locks():
    sources = load_json("sources.lock.json")["sources"]
    packages = load_json("dependencies.lock.json")["packages"]
    if len({s["id"] for s in sources}) != len(sources):
        raise ValueError("Duplicate source ID")
    for source in sources:
        if not re.fullmatch(r"[0-9a-f]{40}", source["revision"]):
            raise ValueError("Source must use a full commit ID")
        if not source["license"]:
            raise ValueError("License review missing")
        if source["download"] and source["id"] != "linux-lumia920":
            raise ValueError("Only the reviewed kernel may be fetched")
    kernel = next(s for s in sources if s["id"] == "linux-lumia920")
    for entry in [kernel] + packages:
        if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise ValueError("Missing SHA-256")
        url = urlparse(entry["url"])
        if (url.scheme != "https" or url.username or url.password
                or url.hostname not in {"codeload.github.com", "deb.debian.org"}):
            raise ValueError("Unreviewed dependency URL")
    for package in packages:
        if Path(package["filename"]).name != package["filename"]:
            raise ValueError("Invalid package filename")
    return kernel, packages


def download(entry, destination):
    destination = confined(ROOT, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if digest(destination) != entry["sha256"]:
            raise ValueError(f"Checksum mismatch: {destination}; cache was not reused")
        return
    partial = destination.with_suffix(destination.suffix + ".part")
    subprocess.run(["curl", "--fail", "--location", "--retry", "2",
                    "--max-time", "600", "--max-filesize", "536870912",
                    "--output", str(partial), entry["url"]], check=True)
    if digest(partial) != entry["sha256"]:
        partial.unlink()
        raise ValueError("Downloaded dependency checksum mismatch")
    partial.replace(destination)


def extract_source(archive, destination, archive_root):
    """Allow confined source links; reject traversal and special files."""
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Refuse to replace an existing source directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                p = Path(member.name)
                if (p.is_absolute() or ".." in p.parts or not p.parts
                        or p.parts[0] != archive_root
                        or not (member.isfile() or member.isdir()
                                or member.issym() or member.islnk())):
                    raise ValueError(f"Unsafe source archive member: {member.name}")
            tar.extractall(tmp, filter="data")
        (Path(tmp) / archive_root).rename(destination)


def setup():
    _, packages = validate_locks()
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("Pinned tools require x86_64 Linux; see docs/build.md")
    require_space(ROOT, 1)
    tools = workpath("tools")
    tools.mkdir(parents=True, exist_ok=True)
    for package in packages:
        cached = workpath("cache/debs") / package["filename"]
        download(package, cached)
        subprocess.run(["dpkg-deb", "-x", str(cached), str(tools)], check=True)
    # Packages are only unpacked locally; maintainer scripts are never run.
    print(f"Verified and unpacked {len(packages)} packages into {tools}")


def fetch():
    kernel, _ = validate_locks()
    require_space(ROOT, 8)
    archive = workpath("cache/linux-lumia920.tar.gz")
    download(kernel, archive)
    source = workpath("sources/linux-lumia920")
    if source.exists():
        if (source / ".source-sha256").read_text().strip() != kernel["sha256"]:
            raise ValueError("Source receipt mismatch")
    else:
        extract_source(archive, source, kernel["archive_root"])
        (source / ".source-sha256").write_text(kernel["sha256"] + "\n")
    print(f"Source pinned at {kernel['revision']}; local edits are not authenticated")


def build_environment():
    tools = workpath("tools") / "usr"
    env = dict(os.environ)
    env.update(PATH=str(tools / "bin") + os.pathsep + env.get("PATH", ""),
               LD_LIBRARY_PATH=str(tools / "lib/x86_64-linux-gnu"),
               BISON_PKGDATADIR=str(tools / "share/bison"),
               M4=str(tools / "bin/m4"),
               KBUILD_BUILD_USER="eos-builder", KBUILD_BUILD_HOST="cloud-build",
               KBUILD_BUILD_TIMESTAMP="2026-08-11 07:21:00 +0000",
               KBUILD_BUILD_VERSION="1", LC_ALL="C", TZ="UTC")
    for name in ("gcc", "make", "arm-linux-gnueabihf-gcc", "flex", "bison", "bc"):
        if not shutil.which(name, path=env["PATH"]):
            raise ValueError(f"Missing {name}; run setup and check host prerequisites")
    return env


def build(target, jobs):
    if target not in TARGETS or not 1 <= jobs <= 4:
        raise ValueError("Only reviewed host compile targets and 1..4 jobs are allowed")
    kernel, _ = validate_locks()
    require_space(ROOT, 8 if target == "kernel" else 2)
    source = workpath("sources/linux-lumia920")
    if (source / ".source-sha256").read_text().strip() != kernel["sha256"]:
        raise ValueError("Fetch the pinned source first")
    env = build_environment()
    output = workpath("build/linux-lumia920")
    logs = workpath("logs")
    logs.mkdir(parents=True, exist_ok=True)
    base = ["make", "-C", str(source), f"O={output}", "ARCH=arm",
            "CROSS_COMPILE=arm-linux-gnueabihf-"]
    commands = []
    if not (output / ".config").exists():
        commands.append(base + ["lumia920_defconfig"])
    commands.append(base + [f"-j{jobs}"] + TARGETS[target])
    stamp = f"{target}-{time.time_ns()}"
    report = dict(source=kernel["revision"], target=target, scope="Lumia 920 compile only",
                  commands=commands, exit_code=None, artifacts=[])
    log = logs / (stamp + ".log")
    print(f"Compile only; no hardware access. Log: {log}", flush=True)
    with log.open("w") as f:
        for command in commands:
            print("+ " + shlex.join(command), file=f, flush=True)
            result = subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT)
            report["exit_code"] = result.returncode
            if result.returncode:
                break
    if report["exit_code"] == 0:
        relative = TARGETS[target] if target == "objects" else (
            ["arch/arm/boot/zImage"] if target == "kernel" else
            ["arch/arm/boot/dts/" + t for t in TARGETS[target]])
        for path in relative:
            artifact = output / path
            report["artifacts"].append(dict(path=path, bytes=artifact.stat().st_size,
                                             sha256=digest(artifact)))
    (logs / (stamp + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report["exit_code"]


def inventory():
    """No hostname, user identity, environment values, network config or identifiers."""
    result = dict(os=platform.system(), architecture=platform.machine(),
                  python=platform.python_version(), cpu_visible=os.cpu_count(),
                  free_disk_bytes=shutil.disk_usage(ROOT).free)
    for name in ("cpu.max", "memory.max"):
        p = Path("/sys/fs/cgroup") / name
        result[name] = p.read_text().strip() if p.exists() else "unavailable"
    for command in ("git", "gcc", "make", "curl"):
        p = subprocess.run([command, "--version"], capture_output=True, text=True)
        result[command] = p.stdout.splitlines()[0] if p.stdout else "unavailable"
    print(json.dumps(result, indent=2))


def check():
    validate_locks()
    files = subprocess.check_output(["git", "ls-files", "--cached", "--others",
                                     "--exclude-standard", "-z"], cwd=ROOT).split(b"\0")
    prohibited = {".img", ".bin", ".ffu", ".hex", ".elf", ".dtb", ".deb", ".pem", ".key"}
    secret = re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|"
                        rb"gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}")
    for raw in filter(None, files):
        relative = Path(os.fsdecode(raw))
        p = ROOT / relative
        if (relative.parts[0] in {".work", ".cache"} or p.suffix.lower() in prohibited
                or p.name.startswith(".env") or p.is_symlink()):
            raise ValueError(f"Excluded publication path: {relative}")
        data = p.read_bytes()
        if len(data) > 1024 * 1024 or b"\0" in data or secret.search(data):
            raise ValueError(f"Review publication content: {relative}")
    print("Pinned inventories and publication checks passed (manual review still required)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory", "setup", "fetch", "build", "check", "android"])
    parser.add_argument("--target", choices=TARGETS, default="dtbs")
    parser.add_argument("--jobs", type=int, choices=range(1, 5), default=4)
    args = parser.parse_args()
    if args.command == "build":
        return build(args.target, args.jobs)
    if args.command == "android":
        print("BLOCKED: no verified EOS kernel/DT, Android device tree, or HAL/license "
              "bundle. No Android release selected. Current AOSP resource baseline: "
              "400 GB free disk and 64 GB RAM. See docs/status.md.", file=sys.stderr)
        return 2
    globals()[args.command]()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
