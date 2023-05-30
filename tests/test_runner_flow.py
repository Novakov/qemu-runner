import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union, Sequence, List

import pytest

from .test_utllities import place_echo_args, with_env, with_cwd

CmdlineArg = Union[str, os.PathLike]


def run_make_runner(*args: CmdlineArg, cwd: Optional[os.PathLike] = None) -> None:
    cp = subprocess.run(
        [sys.executable, '-m', 'qemu_runner.make_runner', *map(str, args)],
        cwd=cwd
    )
    assert cp.returncode == 0


def execute_runner(runner, args: Sequence[CmdlineArg], cwd: Optional[os.PathLike] = None,
                   check: bool = True) -> subprocess.CompletedProcess:
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


def capture_runner_cmdline(runner: Path, *args: CmdlineArg, cwd: Optional[os.PathLike] = None) -> List[str]:
    cp = execute_runner(runner, args, cwd=cwd)

    actual_args = cp.stdout.splitlines(keepends=False)
    return [
        actual_args[0].lower().replace('\\', '/'),
        *actual_args[1:],
    ]


@pytest.fixture()
def test_layer(tmp_path: Path) -> Path:
    with open(tmp_path / 'test-layer', 'w') as f:
        f.write("""
        [general]
        engine = qemu-system-arm
        memory = 128M
        
        [machine]
        @ = virt_cortex_m
        flash_kb = 1024
        """)

    return tmp_path / 'test-layer'


def test_runner_flow(tmp_path: Path, test_layer: Path):
    engine = place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', test_layer, '-o', tmp_path / 'test.pyz', cwd=tmp_path)
    with with_cwd(tmp_path):
        cmdline = capture_runner_cmdline(tmp_path / 'test.pyz', 'abc.elf', 'arg1', 'arg2')

    assert cmdline == [
        engine,
        '-machine', 'virt_cortex_m,flash_kb=1024',
        '-m', '128M',
        '-kernel',  str(tmp_path / 'abc.elf'),
        '-append', 'arg1 arg2'
    ]


def test_runner_flow_no_args(tmp_path: Path, test_layer: Path):
    engine = place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', test_layer, '-o', tmp_path / 'test.pyz', cwd=tmp_path)
    with with_cwd(tmp_path):
        cmdline = capture_runner_cmdline(tmp_path / 'test.pyz', 'abc.elf')

    assert cmdline == [
        engine,
        '-machine', 'virt_cortex_m,flash_kb=1024',
        '-m', '128M',
        '-kernel',  str(tmp_path / 'abc.elf'),
    ]


def assert_arg_set_in_cmdline(arg_set: List[str], cmdline: List[str]):
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
def test_builtin_args(tmpdir: Path, runner_args: List[str], qemu_args: List[List[str]], test_layer: Path):
    place_echo_args(tmpdir / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', test_layer, '-o', tmpdir / 'test.pyz', cwd=tmpdir)
    cmdline = capture_runner_cmdline(tmpdir / 'test.pyz', *runner_args, 'abc.elf', 'arg1', 'arg2')

    for arg_set in qemu_args:
        assert_arg_set_in_cmdline(arg_set, cmdline)


def test_debug_listen_no_debug(tmp_path: Path, test_layer: Path):
    place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', test_layer, '-o', tmp_path / 'test.pyz', cwd=tmp_path)
    cmdline = capture_runner_cmdline(tmp_path / 'test.pyz', '--debug-listen', 'MARK-DEBUG', 'abc.elf', 'arg1', 'arg2')

    assert 'MARK-DEBUG' not in cmdline


def test_layers_are_embbedded_in_runner(tmp_path: Path, test_layer: Path):
    place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    with open(tmp_path / 'my-layer.ini', 'w') as f:
        f.write("""
        [device:test_id]
        @=test_device
        addr=12
        """)

    run_make_runner('-l', test_layer, 'my-layer.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    os.unlink(tmp_path / 'my-layer.ini')

    cmdline = capture_runner_cmdline(tmp_path / 'test.pyz', 'abc.elf', 'arg1', 'arg2')

    assert_arg_set_in_cmdline(['-device', 'test_device,id=test_id,addr=12'], cmdline)


def test_extract_base_command_line_with_kernel(tmp_path: Path, test_layer: Path):
    with open(tmp_path / 'my-layer.ini', 'w') as f:
        f.write("""
        [device:test_id]
        @=test_device
        addr=12
        """)

    run_make_runner('-l', test_layer, 'my-layer.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    with with_env({'QEMU_DEV': 'my-qemu'}), with_cwd(tmp_path):
        cp = execute_runner(tmp_path / 'test.pyz', ['--debug', '--dry-run', 'abc.elf', 'a', 'b', 'c'])

    kernel_path = tmp_path / 'abc.elf'

    assert cp.stdout.strip().replace("-kernel '", '-kernel ').replace("' -append", ' -append') == (
            "my-qemu -machine virt_cortex_m,flash_kb=1024 -device test_device,id=test_id,addr=12 -m 128M " +
            f"-s -kernel {kernel_path} -append 'a b c'")


def test_extract_base_command_line_no_kernel(tmp_path: Path, test_layer: Path):
    with open(tmp_path / 'my-layer.ini', 'w') as f:
        f.write("""
        [device:test_id]
        @=test_device
        addr=12
        """)

    run_make_runner('-l', test_layer, 'my-layer.ini', '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    with with_env({'QEMU_DEV': 'my-qemu'}):
        cp = execute_runner(tmp_path / 'test.pyz', ['--debug', '--dry-run'])

    assert cp.stdout.strip() == ("my-qemu -machine virt_cortex_m,flash_kb=1024 -device test_device,id=test_id,addr=12 " +
                                 "-m 128M -s")


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

    with with_cwd(tmp_path):
        cmdline = capture_runner_cmdline(tmp_path / 'derived.pyz', 'abc.elf')

    assert cmdline == [
        engine,
        '-device', 'test,id=d1',
        '-device', 'test,id=d2',
        '-kernel', str(tmp_path / 'abc.elf'),
    ]


def test_derive_keep_qemu_path(tmp_path: Path):
    engine = place_echo_args(tmp_path / 'dir1' / 'qemu' / 'my-qemu')

    with open(tmp_path / 'layer1.ini', 'w') as f:
        f.write("""
        [general]
        engine = my-qemu

        [device:d1]
        @=test
        """)

    run_make_runner('-l', './layer1.ini', '-o', tmp_path / 'dir1' / 'base_runner.pyz', cwd=tmp_path)

    (tmp_path / 'dir2').mkdir()
    execute_runner(
        tmp_path / 'dir1' / 'base_runner.pyz',
        ['--layers', './layer1.ini', '--derive', './dir2/derived.pyz', '--track-qemu'],
        cwd=tmp_path
    )

    cmdline = capture_runner_cmdline(tmp_path / 'dir2' / 'derived.pyz', 'abc.elf')

    assert cmdline[0] == engine


def test_derive_add_qemu_dir(tmp_path: Path):
    engine = place_echo_args(tmp_path / 'dir1' / 'some-path' / 'my-qemu')

    with open(tmp_path / 'layer1.ini', 'w') as f:
        f.write("""
        [general]
        engine = my-qemu

        [device:d1]
        @=test
        """)

    (tmp_path / 'dir2').mkdir()

    run_make_runner('-l', './layer1.ini', '-o', tmp_path / 'dir2' / 'base_runner.pyz', cwd=tmp_path)

    execute_runner(
        tmp_path / 'dir2' / 'base_runner.pyz',
        ['--layers', './layer1.ini', '--derive', './dir2/derived.pyz', '--qemu-dir', tmp_path / 'dir1' / 'some-path'],
        cwd=tmp_path
    )

    cmdline = capture_runner_cmdline(tmp_path / 'dir2' / 'derived.pyz', 'abc.elf')

    assert cmdline[0] == engine


def test_preserve_additional_search_path_in_next_derived_runner(tmp_path: Path):
    engine = place_echo_args(tmp_path / 'dir1' / 'some-path' / 'my-qemu')

    with open(tmp_path / 'layer1.ini', 'w') as f:
        f.write("""
        [general]
        engine = my-qemu

        [device:d1]
        @=test
        """)

    (tmp_path / 'dir2').mkdir()

    run_make_runner('-l', './layer1.ini', '-o', tmp_path / 'dir2' / 'base_runner.pyz', cwd=tmp_path)

    execute_runner(
        tmp_path / 'dir2' / 'base_runner.pyz',
        ['--layers', './layer1.ini', '--derive', './dir2/derived1.pyz', '--qemu-dir', tmp_path / 'dir1' / 'some-path'],
        cwd=tmp_path
    )

    execute_runner(
        tmp_path / 'dir2' / 'derived1.pyz',
        ['--layers', './layer1.ini', '--derive', './dir2/derived2.pyz', '--qemu-dir', tmp_path / 'dir2' / 'some-path'],
        cwd=tmp_path
    )

    cmdline = capture_runner_cmdline(tmp_path / 'dir2' / 'derived2.pyz', 'abc.elf')

    assert cmdline[0] == engine


def test_env_qemu_flags(tmp_path: Path):
    engine = place_echo_args(tmp_path / 'qemu' / 'my-qemu')

    with open(tmp_path / 'layer1.ini', 'w') as f:
        f.write("""
        [general]
        engine = my-qemu

        [machine]
        @=test
        """)

    run_make_runner('-l', './layer1.ini', '-o', tmp_path / 'runner.pyz', cwd=tmp_path)
    with with_env({'QEMU_FLAGS': '-s -device test,id=2'}), with_cwd(tmp_path):
        cmdline = capture_runner_cmdline(tmp_path / 'runner.pyz', 'abc.elf')

    assert cmdline == [
        engine,
        '-s',
        '-device', 'test,id=2',
        '-machine', 'test',
        '-kernel', str(tmp_path / 'abc.elf')
    ]


def test_env_runner_flags(tmp_path: Path):
    engine = place_echo_args(tmp_path / 'qemu' / 'my-qemu')

    with open(tmp_path / 'layer1.ini', 'w') as f:
        f.write("""
        [general]
        engine = my-qemu

        [machine]
        @=test
        """)

    run_make_runner('-l', './layer1.ini', '-o', tmp_path / 'runner.pyz', cwd=tmp_path)
    with with_env({'QEMU_RUNNER_FLAGS': '--halted --debug'}), with_cwd(tmp_path):
        cmdline = capture_runner_cmdline(tmp_path / 'runner.pyz', 'abc.elf')

    assert cmdline == [
        engine,
        '-machine', 'test',
        '-S',
        '-s',
        '-kernel', str(tmp_path / 'abc.elf')
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
def test_invalid_args(tmp_path: Path, args: List[str], test_layer: Path) -> None:
    run_make_runner('-l', test_layer, '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    cp = execute_runner(tmp_path / 'test.pyz', args, check=False, cwd=tmp_path)
    assert 'test.pyz: error:' in cp.stderr
    assert cp.returncode != 0


def test_explicit_qemu_dir(tmp_path: Path, test_layer: Path) -> None:
    engine = place_echo_args(tmp_path / 'my-qemu' / 'qemu-system-arm')

    run_make_runner('-l', test_layer, '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    args = capture_runner_cmdline(tmp_path / 'test.pyz', '--qemu-dir', tmp_path / 'my-qemu', 'abc.elf')

    assert args[0] == engine


def test_explicit_qemu_executable(tmp_path: Path, test_layer: Path) -> None:
    engine = place_echo_args(tmp_path / 'my-qemu' / 'qemu')

    run_make_runner('-l', test_layer, '-o', tmp_path / 'test.pyz', cwd=tmp_path)

    args = capture_runner_cmdline(tmp_path / 'test.pyz', '--qemu', engine, 'abc.elf')

    assert args[0] == engine


def test_resolve_kernel_dir_to_absolute_path(tmp_path: Path) -> None:
    engine = place_echo_args(tmp_path / 'qemu' / 'my-qemu')

    with open(tmp_path / 'layer1.ini', 'w') as f:
        f.write("""
            [general]
            engine = my-qemu

            [machine]
            @=test
            
            [device]
            @=path
            value=${KERNEL_DIR}/dir/file.bin
            """)

    run_make_runner('-l', './layer1.ini', '-o', tmp_path / 'runner.pyz', cwd=tmp_path)

    with with_cwd(tmp_path):
        args = capture_runner_cmdline(tmp_path / 'runner.pyz', 'kernel/abc.elf')

    idx = args.index('-device')
    resolved_arg = args[idx + 1]

    file_bin = tmp_path / 'kernel' / 'dir' / 'file.bin'

    assert resolved_arg.replace('\\', '/') == f'path,value={file_bin}'.replace('\\', '/')
