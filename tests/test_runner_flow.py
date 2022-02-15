import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union

import pytest

from .test_utllities import place_echo_args

CmdlineArg = Union[str, os.PathLike]


def run_make_runner(*args: CmdlineArg, cwd: Optional[os.PathLike] = None) -> None:
    cp = subprocess.run(
        [sys.executable, '-m', 'qemu_runner.make_runner', *map(str, args)],
        cwd=cwd
    )
    assert cp.returncode == 0


def capture_runner_cmdline(runner: Path, *args: CmdlineArg, cwd: Optional[os.PathLike] = None) -> list[str]:
    cp = subprocess.run(
        [sys.executable, str(runner), *map(str, args)],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8'
    )

    assert cp.stderr == ''

    actual_args = cp.stdout.splitlines(keepends=False)
    return [
        actual_args[0].lower().replace('\\', '/'),
        *actual_args[1:],
    ]


def test_runner_flow(tmp_path: Path):
    engine = place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', 'virt-cortex-m.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)
    cmdline = capture_runner_cmdline(tmp_path / 'test.pyz', 'abc.elf', 'arg1', 'arg2')

    assert cmdline == [
        engine,
        '-machine', 'virt_cortex_m,flash_kb=1024',
        '-kernel', 'abc.elf',
        '-append', 'arg1 arg2'
    ]


def assert_arg_set_in_cmdline(arg_set: list[str], cmdline: list[str]):
    if len(arg_set) == 1:
        assert arg_set[0] in cmdline
    else:
        leader = arg_set[0]
        assert leader in cmdline
        idx = cmdline.index(leader)
        assert cmdline[idx:idx + len(arg_set)] == arg_set


@pytest.mark.parametrize(('runner_args', 'qemu_args'), [
    (['--halted'], [['-S']]),
    (['--debug'], [['-s']]),
    (['--debug', '--debug-listen', 'abc'], [['-gdb', 'abc']]),
])
def test_builtin_args(tmpdir: Path, runner_args: list[str], qemu_args: list[list[str]]):
    place_echo_args(tmpdir / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', 'virt-cortex-m.ini', '-o', tmpdir / 'test.pyz', cwd=tmpdir)
    cmdline = capture_runner_cmdline(tmpdir / 'test.pyz', *runner_args, 'abc.elf', 'arg1', 'arg2')

    for arg_set in qemu_args:
        assert_arg_set_in_cmdline(arg_set, cmdline)


def test_debug_listen_no_debug(tmpdir: Path):
    place_echo_args(tmpdir / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', 'virt-cortex-m.ini', '-o', tmpdir / 'test.pyz', cwd=tmpdir)
    cmdline = capture_runner_cmdline(tmpdir / 'test.pyz', '--debug-listen', 'MARK-DEBUG', 'abc.elf', 'arg1', 'arg2')

    assert 'MARK-DEBUG' not in cmdline


def test_layers_are_embbedded_in_runner(tmpdir: Path):
    place_echo_args(tmpdir / 'qemu' / 'qemu-system-arm')

    with open(tmpdir / 'my-layer.ini', 'w') as f:
        f.write("""
        [device:test_id]
        @=test_device
        addr=12
        """)

    run_make_runner('-l', 'virt-cortex-m.ini', 'my-layer.ini', '-o', tmpdir / 'test.pyz', cwd=tmpdir)

    os.unlink(tmpdir / 'my-layer.ini')

    cmdline = capture_runner_cmdline(tmpdir / 'test.pyz', 'abc.elf', 'arg1', 'arg2')

    assert_arg_set_in_cmdline(['-device', 'test_device,id=test_id,addr=12'], cmdline)
