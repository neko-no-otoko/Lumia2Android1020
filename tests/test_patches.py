"""Failure-path tests for reviewed kernel patches; real DT checks run separately."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("lumia", Path(__file__).resolve().parents[1] / "scripts/lumia.py")
lumia = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lumia)


class PatchTests(unittest.TestCase):
    def test_pinned_patch_metadata(self):
        self.assertGreaterEqual(len(lumia.patch_entries()), 1)

    def test_wrong_source_fails_before_patch_executes(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / "fixture").write_text("unexpected local change\n")
            entry = {"files": [{"path": "fixture", "before_sha256": "0" * 64}]}
            with mock.patch.object(lumia.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "precondition"):
                    lumia.apply_source_patch(source, entry)
                run.assert_not_called()
            self.assertEqual((source / "fixture").read_text(), "unexpected local change\n")

    def test_changed_patch_hash_is_rejected(self):
        original = lumia.load_json
        lock = original("patches.lock.json")
        lock["patches"][0]["sha256"] = "0" * 64
        with mock.patch.object(lumia, "load_json", side_effect=lambda name:
                               lock if name == "patches.lock.json" else original(name)):
            with self.assertRaisesRegex(ValueError, "hash"):
                lumia.patch_entries()

    def test_unreviewed_patch_headers_are_rejected(self):
        for extra in ("--- /dev/sda\n+++ /dev/sda\n", "--- a/other\n+++ b/other\n"):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                p = root / "fixture.patch"
                p.write_text("--- a/reviewed\n+++ b/reviewed\n" + extra)
                lock = {"source_revision": "1" * 40, "patches": [{
                    "path": p.name, "sha256": lumia.digest(p), "license": "GPL-2.0-only",
                    "files": [{"path": "reviewed"}]}]}
                with mock.patch.object(lumia, "ROOT", root), \
                        mock.patch.object(lumia, "validate_locks", return_value=({"revision": "1" * 40}, [])), \
                        mock.patch.object(lumia, "load_json", return_value=lock):
                    with self.assertRaises(ValueError):
                        lumia.patch_entries()


if __name__ == "__main__":
    unittest.main()
