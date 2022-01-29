import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union


def place_echo_args(file_path: Path) -> str:
    source = 'D:/Coding/echo-args/build/Debug/echo_args.exe'

    ext = ''
    if sys.platform == 'win32':
        ext = '.exe'

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    dst = Path(file_path).with_suffix(ext)
    shutil.copy(src=source, dst=dst)

    return str(dst).lower().replace('\\', '/')


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
        encoding='utf-8'
    )

    return cp.stdout.lower().replace('\\', '/').splitlines(keepends=False)


def test_runner_flow(tmpdir: Path):
    engine = place_echo_args(tmpdir / 'qemu' / 'qemu-system-arm')

    run_make_runner('-l', 'virt-cortex-m.ini', '-o', tmpdir / 'test.pyz', cwd=tmpdir)
    cmdline = capture_runner_cmdline(tmpdir / 'test.pyz', 'abc.elf', 'arg1', 'arg2')

    assert cmdline == [
        engine,
        '-machine', 'virt_cortex_m,flash_kb=1024',
        '-kernel', 'abc.elf',
        '-append', 'arg1 arg2'
    ]

