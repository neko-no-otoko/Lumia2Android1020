#!/usr/bin/env python3
"""Pinned generic ARM32 virtual smoke tests. No Lumia emulation or device access."""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse
import lumia

BASE = lumia.workpath('emulation')
ROOT = lumia.ROOT
EXPECTED = ('identity', 'mounts', 'memory', 'fork_pipe', 'smp_affinity',
            'clock_epoll', 'namespace', 'binder_abi')


def lock():
    data = lumia.load_json('emulation.lock.json')
    if (data['machine'] != 'virt-10.0,highmem=off,gic-version=2' or data['cpu'] != 'cortex-a15'
            or data['accelerator'] != 'tcg,thread=multi' or data['memory_mib'] != 256 or data['cpus'] != 2):
        raise ValueError('Only the reviewed generic ARM32 machine is allowed')
    for item in [data['source']] + data['packages']:
        url = urlparse(item['url'])
        if url.scheme != 'https' or url.hostname not in {'deb.debian.org', 'codeload.github.com'} or url.username or url.password:
            raise ValueError('Unreviewed download URL')
        if not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            raise ValueError('Missing pinned artifact hash')
    for item in data['packages']:
        if item['role'] not in ('runtime', 'cross') or Path(item['filename']).name != item['filename']:
            raise ValueError('Invalid extraction role/path')
    return data


def setup():
    data = lock()
    lumia.require_space(ROOT, 4)
    for item in data['packages']:
        cached = BASE / 'cache/debs' / item['filename']
        lumia.download(item, cached)
        subprocess.run(['dpkg-deb', '-x', str(cached), str(BASE / item['role'])], check=True)
        if lumia.digest(BASE / item['role'] / item['license_notice']) != item['license_notice_sha256']:
            raise ValueError('Pinned license notice changed')
    archive = BASE / 'cache/linux-v6.6.tar.gz'
    lumia.download(data['source'], archive)
    source = BASE / 'linux'
    if not source.exists():
        lumia.extract_source(archive, source, data['source']['archive_root'])
        (source / '.source-sha256').write_text(data['source']['sha256']+'\n')
    if (source / '.source-sha256').read_text().strip() != data['source']['sha256']:
        raise ValueError('Source receipt mismatch')
    cmd = qemu()
    linked = subprocess.run(cmd[:3]+['--list', cmd[3]], check=True, text=True, stdout=subprocess.PIPE)
    for line in linked.stdout.splitlines():
        if '=>' in line:
            resolved = Path(line.split('=>', 1)[1].split()[0]).resolve()
            if not resolved.is_relative_to(BASE / 'runtime'):
                raise ValueError('Emulator unexpectedly depends on an unpinned host library')
    print('Pinned packages unpacked locally; no maintainer scripts or account creation')


def qemu():
    runtime = BASE / 'runtime'
    libs = runtime / 'usr/lib/x86_64-linux-gnu'
    return [str(libs / 'ld-linux-x86-64.so.2'), '--library-path',
            str(libs)+':'+str(runtime / 'usr/lib'),
            str(runtime / 'usr/bin/qemu-system-arm'), '-L', str(runtime / 'usr/share/qemu')]


def build():
    lock()
    lumia.require_space(ROOT, 3)
    source, out = BASE / 'linux', BASE / 'build'
    out.mkdir(parents=True, exist_ok=True)
    env = lumia.build_environment()
    env['KCONFIG_ALLCONFIG'] = str(ROOT / 'emulation/virt.config')
    commands = [
        ['make', '-C', str(source), 'O='+str(out), 'ARCH=arm', 'CROSS_COMPILE=arm-linux-gnueabihf-', 'allnoconfig'],
        ['make', '-C', str(source), 'O='+str(out), 'ARCH=arm', 'CROSS_COMPILE=arm-linux-gnueabihf-', '-j4', 'zImage'],
    ]
    cross = BASE / 'cross/usr/arm-linux-gnueabihf'
    commands.append(['arm-linux-gnueabihf-gcc', '-static', '-O2', '-Wall', '-Wextra', '-Werror',
                     '-isystem', str(cross / 'include'), '-B'+str(cross / 'lib')+'/',
                     '-L'+str(cross / 'lib'), str(ROOT / 'emulation/init.c'), '-o', str(BASE / 'init')])
    log = BASE / 'build.log'
    with log.open('w') as stream:
        for cmd in commands:
            stream.write('$ '+repr(cmd)+'\n'); stream.flush()
            subprocess.run(cmd, env=env, check=True, stdout=stream, stderr=stream, timeout=1200)
            if cmd[-1] == 'allnoconfig':
                verify_config((out / '.config').read_text())
    data = (BASE / 'init').read_bytes()
    (BASE / 'initramfs.cpio.gz').write_bytes(gzip.compress(cpio([('init', data, 0o100755)]), mtime=0))
    print('Built pristine generic Linux and original static ARM userspace; '+str(log))


def verify_config(text):
    expected = [line for line in (ROOT / 'emulation/virt.config').read_text().splitlines() if line.startswith('CONFIG_')]
    missing = sorted(set(expected)-set(text.splitlines()))
    if missing:
        raise ValueError('Kconfig dropped requested virtual-test prerequisites: '+', '.join(missing))


def cpio(entries):
    """Deterministic newc archive; names cannot escape the guest root."""
    result = bytearray()
    for index, (name, payload, mode) in enumerate(list(entries)+[('TRAILER!!!', b'', 0)]):
        if name.startswith('/') or '..' in Path(name).parts or '\x00' in name:
            raise ValueError('Unsafe initramfs member')
        encoded = name.encode()+b'\0'
        fields = [index+1, mode, 0, 0, 1, 0, len(payload), 0, 0, 0, 0, len(encoded), 0]
        result.extend(('070701'+''.join(f'{value:08x}' for value in fields)).encode())
        result.extend(encoded); result.extend(b'\0'*(-len(result)%4))
        result.extend(payload); result.extend(b'\0'*(-len(result)%4))
    return bytes(result)


def command(negative=False):
    data = lock()
    return qemu()+['-machine', data['machine'], '-cpu', data['cpu'], '-accel', data['accelerator'],
                   '-smp', str(data['cpus']), '-m', str(data['memory_mib']), '-display', 'none',
                   '-serial', 'stdio', '-monitor', 'none', '-nic', 'none', '-no-reboot',
                   '-kernel', str(BASE / 'build/arch/arm/boot/zImage'),
                   '-initrd', str(BASE / 'initramfs.cpio.gz'),
                   '-append', 'console=ttyAMA0 panic=-1 rdinit='+('/missing-init' if negative else '/init')]


def check_log(log, returncode):
    if returncode != 0 or 'Kernel panic' in log or 'SMOKE_FAIL' in log or 'HARNESS_TIMEOUT' in log:
        raise ValueError('Guest failed, panicked or emulator exited unsuccessfully')
    markers = re.findall(r'^SMOKE_OK ([a-z_]+)\r?$', log, re.M)
    if sorted(markers) != sorted(EXPECTED) or log.count('SMOKE_COMPLETE\n') != 1:
        raise ValueError('Missing/duplicated guest assertions; boot text alone is not success')
    if 'reboot: Power down' not in log:
        raise ValueError('Guest did not reach orderly poweroff')


def run():
    report = dict(scope='Generic ARMv7 Linux on QEMU virt, not Lumia or Android framework', runs=[])
    env = dict(os.environ, QEMU_MODULE_DIR=str(BASE / 'runtime/usr/lib/x86_64-linux-gnu/qemu'))
    for negative in (False, True):
        cmd = command(negative)
        name = 'missing-init' if negative else 'smoke'
        path = BASE / (name+'.log')
        try:
            result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        except subprocess.TimeoutExpired as error:
            path.write_text((error.stdout or b'').decode(errors='replace')+'\nHARNESS_TIMEOUT\n')
            raise ValueError('Emulator timed out; partial serial log retained') from error
        output = result.stdout.decode(errors='replace').replace('\r\n', '\n')
        path.write_text(output)
        if negative:
            if result.returncode != 0:
                raise ValueError('Negative control emulator itself failed')
            try:
                check_log(output, result.returncode)
            except ValueError:
                if 'Kernel panic' not in output:
                    raise ValueError('Negative control failed before the expected kernel panic')
            else:
                raise ValueError('Negative control incorrectly accepted')
        else:
            check_log(output, result.returncode)
        report['runs'].append(dict(name=name, command=cmd, emulator_exit=result.returncode,
                                   result='expected panic rejected' if negative else 'PASS', log_sha256=lumia.digest(path)))
    report['artifacts'] = {name: dict(bytes=(BASE / name).stat().st_size, sha256=lumia.digest(BASE / name))
                           for name in ['build/arch/arm/boot/zImage', 'build/.config', 'init', 'initramfs.cpio.gz']}
    (BASE / 'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('step', choices=['setup', 'build', 'run', 'machines'])
    args = parser.parse_args()
    if args.step == 'machines':
        subprocess.run(qemu()+['-machine', 'help'], check=True)
    else:
        globals()[args.step]()
