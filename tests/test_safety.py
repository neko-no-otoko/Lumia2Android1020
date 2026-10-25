"""Synthetic tests; these do not establish handset safety or hardware support."""
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/lumia.py"
spec = importlib.util.spec_from_file_location("lumia", SCRIPT)
lumia = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lumia)


class SafetyTests(unittest.TestCase):
    def test_valid_locks(self):
        kernel, packages = lumia.validate_locks()
        self.assertEqual(kernel["role"], "compile-reference")
        self.assertGreater(len(packages), 0)

    def test_refuse_device_or_escaping_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in ("/dev/sda", root / "..", root):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    lumia.confined(root, path)
            (root / "escape").symlink_to("/dev", target_is_directory=True)
            with self.assertRaises(ValueError):
                lumia.confined(root, root / "escape/sda")

    def test_low_disk_stops_before_download(self):
        with mock.patch.object(lumia.shutil, "disk_usage") as disk:
            disk.return_value.free = lumia.GIB
            with self.assertRaisesRegex(ValueError, "8 GiB"):
                lumia.require_space(".", 8)

    def test_cached_hash_mismatch_never_runs_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "download"
            p.write_bytes(b"altered synthetic fixture")
            with mock.patch.object(lumia, "ROOT", Path(tmp)), \
                    mock.patch.object(lumia.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
                    lumia.download({"sha256": "0" * 64}, p)
                run.assert_not_called()

    def test_downloaded_hash_mismatch_is_cleaned_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def corrupt_download(command, **kwargs):
                Path(command[command.index("--output") + 1]).write_bytes(b"corrupt fixture")
            with mock.patch.object(lumia, "ROOT", root), \
                    mock.patch.object(lumia.subprocess, "run", side_effect=corrupt_download):
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    lumia.download({"sha256": "0" * 64, "url": "https://deb.debian.org/fixture"},
                                   root / "cache/file")
            self.assertFalse((root / "cache/file").exists())
            self.assertEqual(list((root / "cache").iterdir()), [])

    def archive(self, directory, name="source/file", kind=tarfile.REGTYPE, link=""):
        p = Path(directory) / "fixture.tar"
        with tarfile.open(p, "w") as tar:
            entry = tarfile.TarInfo(name)
            entry.type, entry.linkname = kind, link
            data = b"synthetic"
            entry.size = len(data) if kind == tarfile.REGTYPE else 0
            tar.addfile(entry, io.BytesIO(data) if entry.size else None)
        return p

    def test_archive_traversal_and_special_files_rejected(self):
        for name, kind in [("../escaped", tarfile.REGTYPE),
                           ("/absolute", tarfile.REGTYPE),
                           ("source/device", tarfile.CHRTYPE)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                archive = self.archive(tmp, name, kind)
                with self.assertRaises(ValueError):
                    lumia.extract_source(archive, Path(tmp) / "out", "source")
                self.assertFalse((Path(tmp) / "out").exists())

    def test_archive_escaping_symlink_rejected(self):
        for link in ("../../escape", "../outside", "/dev/sda"):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as tmp:
                archive = self.archive(tmp, "source/link", tarfile.SYMTYPE, link)
                with self.assertRaises((ValueError, tarfile.FilterError)):
                    lumia.extract_source(archive, Path(tmp) / "out", "source")

    def test_archive_internal_symlink_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.archive(tmp, "source/link", tarfile.SYMTYPE, "file")
            out = Path(tmp) / "out"
            lumia.extract_source(archive, out, "source")
            self.assertTrue((out / "link").is_symlink())
            with self.assertRaises(ValueError):
                lumia.extract_source(archive, out, "source")

    def test_forbidden_build_target_never_executes(self):
        with mock.patch.object(lumia.subprocess, "run") as run:
            for target in ("flash", "/dev/sda", "arm64", "install"):
                with self.subTest(target=target), self.assertRaises(ValueError):
                    lumia.build(target, 4)
            run.assert_not_called()

    def test_reference_cannot_be_enabled_for_download(self):
        sources = lumia.load_json("sources.lock.json")
        sources["sources"][1]["download"] = True
        original = lumia.load_json
        with mock.patch.object(lumia, "load_json", side_effect=lambda name:
                               sources if name == "sources.lock.json" else original(name)):
            with self.assertRaisesRegex(ValueError, "reviewed kernel"):
                lumia.validate_locks()

    def test_android_fails_with_concrete_blocker(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "android"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no verified EOS", result.stderr)
        self.assertIn("400 GB", result.stderr)


if __name__ == "__main__":
    unittest.main()
