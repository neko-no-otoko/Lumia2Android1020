"""Adversarial boot-harness tests, independent of optional QEMU installation."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import virtual_smoke as v


def success():
    return ''.join('SMOKE_OK '+name+'\n' for name in v.EXPECTED)+'SMOKE_COMPLETE\nreboot: Power down\n'


class VirtualHarnessTests(unittest.TestCase):
    def test_zero_emulator_exit_cannot_hide_kernel_panic_or_guest_failure(self):
        for log, code in [(success()+'Kernel panic\n', 0), (success()+'SMOKE_FAIL memory\n', 0),
                          (success()+'HARNESS_TIMEOUT\n', 0), (success(), 1)]:
            with self.assertRaises(ValueError):
                v.check_log(log, code)

    def test_boot_banner_or_partial_duplicate_results_do_not_count_as_pass(self):
        v.check_log(success(), 0)
        for log in ['Linux version6.6.0\n', success().replace('SMOKE_OK memory\n', ''),
                    success()+'SMOKE_OK memory\n', success().replace('reboot: Power down\n', ''),
                    success().replace('SMOKE_COMPLETE\n', '')]:
            with self.assertRaises(ValueError):
                v.check_log(log, 0)

    def test_initramfs_is_deterministic_and_rejects_guest_path_escape(self):
        entries = [('init', b'synthetic', 0o100755)]
        self.assertEqual(v.cpio(entries), v.cpio(entries))
        self.assertTrue(v.cpio(entries).startswith(b'070701'))
        for name in ['/init', '../init', 'sub/../../init', 'in\x00it']:
            with self.assertRaises(ValueError):
                v.cpio([(name, b'', 0)])

    def test_unreviewed_machine_resources_or_downloads_fail_before_execution(self):
        original = v.lock()
        for key, value in [('machine', 'lumia'), ('cpu', 'max'), ('accelerator', 'kvm'),
                           ('memory_mib', 16384), ('cpus', 32)]:
            data = copy.deepcopy(original); data[key] = value
            with patch.object(v.lumia, 'load_json', return_value=data), self.assertRaises(ValueError):
                v.lock()
        data = copy.deepcopy(original); data['source']['url'] = 'http://example.invalid/firmware'
        with patch.object(v.lumia, 'load_json', return_value=data), self.assertRaises(ValueError):
            v.lock()

    def test_command_has_no_disk_network_monitor_or_firmware_backend(self):
        command = v.command()
        self.assertEqual(command[command.index('-nic')+1], 'none')
        self.assertEqual(command[command.index('-monitor')+1], 'none')
        self.assertEqual(command[command.index('-accel')+1], 'tcg,thread=multi')
        for option in ['-drive', '-blockdev', '-netdev', '-bios', '-pflash', '-hda', '-device']:
            self.assertNotIn(option, command)
        self.assertIn('rdinit=/missing-init', v.command(True)[-1])

    def test_requested_kconfig_is_checked_after_dependency_resolution(self):
        text = (v.ROOT / 'emulation/virt.config').read_text()
        v.verify_config(text)
        for setting in ['CONFIG_ANDROID_BINDER_IPC=y', 'CONFIG_ARCH_VIRT=y', 'CONFIG_SMP=y']:
            with self.assertRaises(ValueError):
                v.verify_config(text.replace(setting, '# '+setting.replace('=y', ' is not set')))
