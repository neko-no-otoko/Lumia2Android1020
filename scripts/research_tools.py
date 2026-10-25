#!/usr/bin/env python3
"""Unpack pinned native analysis tools locally, without package maintainer scripts."""
import json
import os
import subprocess
import re
from pathlib import Path
import lumia


def environment():
    root = lumia.workpath("research/tools/usr")
    env = dict(os.environ)
    env.update(PATH=str(root / "bin") + os.pathsep + env.get("PATH", ""),
               LD_LIBRARY_PATH=str(root / "lib/x86_64-linux-gnu"), LC_ALL="C")
    return env


def setup():
    lumia.require_space(lumia.ROOT, 1)
    for entry in lumia.load_json("research-tools.lock.json")["packages"]:
        if (not entry["url"].startswith("https://deb.debian.org/debian/pool/")
                or Path(entry["filename"]).name != entry["filename"]
                or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
                or not entry.get("license")):
            raise ValueError("Unreviewed native analysis package URL")
        cached = lumia.workpath("research/tool-debs") / entry["filename"]
        lumia.download(entry, cached)
        subprocess.run(["dpkg-deb", "-x", str(cached), str(lumia.workpath("research/tools"))], check=True)
    print("Pinned cabextract/libmspack/ACPICA tools unpacked; no phone code executed")


if __name__ == "__main__":
    setup()
