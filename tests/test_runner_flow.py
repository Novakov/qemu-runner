import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union, Sequence, List

import pytest

from .test_utllities import place_echo_args, with_env

CmdlineArg = Union[str, os.PathLike]


def run_make_runner(*args: CmdlineArg, cwd: Optional[os.PathLike] = None) -> None:
    cp = subprocess.run(
        [sys.executable, '-m', 'qemu_runner.make_runner', *map(str, args)],
        cwd=cwd
    )
    assert cp.returncode == 0


def execute_runner(runner, args: Sequence[CmdlineArg], cwd: Optional[os.PathLike] = None, check: bool = True) -> subprocess.CompletedProcess:
    cp = subprocess.run(
        [sys.executable, str(runner), *map(str, args)],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8'
    )
    if check:
        assert cp.stderr == ''
        assert cp.returncode == 0

    return cp


def capture_runner_cmdline(runner: Path, *args: CmdlineArg, cwd: Optional[os.PathLike] = None) -> list[str]:
    cp = execute_runner(runner, args, cwd=cwd)

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


def test_runner_flow_no_args(tmp_path: Path):
    engine = place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', 'virt-cortex-m.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)
    cmdline = capture_runner_cmdline(tmp_path / 'test.pyz', 'abc.elf')

    assert cmdline == [
        engine,
        '-machine', 'virt_cortex_m,flash_kb=1024',
        '-kernel', 'abc.elf',
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


def test_debug_listen_no_debug(tmp_path: Path):
    place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', 'virt-cortex-m.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)
    cmdline = capture_runner_cmdline(tmp_path / 'test.pyz', '--debug-listen', 'MARK-DEBUG', 'abc.elf', 'arg1', 'arg2')

    assert 'MARK-DEBUG' not in cmdline


def test_layers_are_embbedded_in_runner(tmp_path: Path):
    place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    with open(tmp_path / 'my-layer.ini', 'w') as f:
        f.write("""
        [device:test_id]
        @=test_device
        addr=12
        """)

    run_make_runner('-l', 'virt-cortex-m.ini', 'my-layer.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    os.unlink(tmp_path / 'my-layer.ini')

    cmdline = capture_runner_cmdline(tmp_path / 'test.pyz', 'abc.elf', 'arg1', 'arg2')

    assert_arg_set_in_cmdline(['-device', 'test_device,id=test_id,addr=12'], cmdline)


def test_extract_base_command_line_with_kernel(tmp_path: Path):
    with open(tmp_path / 'my-layer.ini', 'w') as f:
        f.write("""
        [device:test_id]
        @=test_device
        addr=12
        """)

    run_make_runner('-l', 'virt-cortex-m.ini', 'my-layer.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    with with_env({'QEMU_DEV': 'my-qemu'}):
        cp = execute_runner(tmp_path / 'test.pyz', ['--debug', '--dry-run', 'abc.elf', 'a', 'b', 'c'])

    assert cp.stdout.strip() == (
                "my-qemu -machine virt_cortex_m,flash_kb=1024 -device test_device,id=test_id,addr=12 " +
                "-s -kernel abc.elf -append 'a b c'")


def test_extract_base_command_line_no_kernel(tmp_path: Path):
    with open(tmp_path / 'my-layer.ini', 'w') as f:
        f.write("""
        [device:test_id]
        @=test_device
        addr=12
        """)

    run_make_runner('-l', 'virt-cortex-m.ini', 'my-layer.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    with with_env({'QEMU_DEV': 'my-qemu'}):
        cp = execute_runner(tmp_path / 'test.pyz', ['--debug', '--dry-run'])

    assert cp.stdout.strip() == "my-qemu -machine virt_cortex_m,flash_kb=1024 -device test_device,id=test_id,addr=12 -s"


def test_derive_runner(tmp_path: Path):
    engine = place_echo_args(tmp_path / 'qemu' / 'my-qemu')

    with open(tmp_path / 'layer1.ini', 'w') as f:
        f.write("""
        [general]
        engine = my-qemu

        [device:d1]
        @=test
        """)

    with open(tmp_path / 'layer2.ini', 'w') as f:
        f.write("""
        [device:d2]
        @=test
        """)

    run_make_runner('-l', './layer1.ini', '-o', tmp_path / 'base_runner.pyz', cwd=tmp_path)

    execute_runner(
        tmp_path / 'base_runner.pyz', ['--layers', './layer2.ini', '--derive', './derived.pyz'],
        cwd=tmp_path
    )

    cmdline = capture_runner_cmdline(tmp_path / 'derived.pyz', 'abc.elf')

    assert cmdline == [
        engine,
        '-device', 'test,id=d1',
        '-device', 'test,id=d2',
        '-kernel', 'abc.elf',
    ]


@pytest.mark.parametrize('args', [
    ['--inspect', '--derive', 'abc.pyz'],
    ['--derive', 'abc.pyz', 'kernel.elf'],
    ['--derive', 'abc.pyz', 'kernel.elf', 'a', 'b'],
    ['--inspect', '--dry-run'],
    ['--derive', 'abc.pyz', '--dry-run'],
    ['--inspect', 'kernel.elf'],
    ['--inspect', 'kernel.elf', 'a', 'b'],

    # ['--derive', 'abc.pyz', '--halted'],
    # ['--derive', 'abc.pyz', '--debug'],
    # ['--derive', 'abc.pyz', '--debug-listen', 'abc'],
    #
    # ['--inspect', '--halted'],
    # ['--inspect', '--debug'],
    # ['--inspect', '--debug-listen', 'abc'],

    ['--halted'],
    ['--debug'],
    ['--debug-listen', 'abc']
])
def test_invalid_args(tmp_path: Path, args: List[str]) -> None:
    run_make_runner('-l', 'virt-cortex-m.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    cp = execute_runner(tmp_path / 'test.pyz', args, check=False, cwd=tmp_path)
    assert 'test.pyz: error:' in cp.stderr
    assert cp.returncode != 0
