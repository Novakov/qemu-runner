import os
from pathlib import Path

import pytest

from qemu_runner import find_qemu

from .test_utllities import place_echo_args, with_env

ENGINE = 'qemu-system-abc'


def do_find_qemu(look_from: Path) -> Path:
    return find_qemu(ENGINE, [str(look_from / 'check.py')])


@pytest.mark.parametrize('subdir', [
    Path(''),
    Path('a'),
    Path('a/b'),
])
def test_abc(tmp_path: Path, subdir: Path):
    qemu = place_echo_args(tmp_path / 'qemu' / ENGINE)
    p = do_find_qemu(tmp_path / subdir)
    assert p == Path(qemu)


@pytest.mark.parametrize('subdir', [
    Path(''),
    Path('a'),
    Path('a/b'),
])
def test_env_qemu_dir(tmp_path: Path, subdir: Path):
    with with_env({'QEMU_DIR': str(tmp_path / 'qemu_dir')}):
        qemu = place_echo_args(tmp_path / 'qemu_dir' / ENGINE)
        p = do_find_qemu(tmp_path / subdir)
        assert p == Path(qemu)


def test_env_qemu_dev(tmp_path: Path):
    qemu = place_echo_args(tmp_path / 'qemu-dev' / 'qemu-some-file')

    with with_env({'QEMU_DEV': str(qemu)}):
        p = do_find_qemu(tmp_path)
        assert p == Path(qemu)


def test_env_qemu_dev_file_not_exist(tmp_path: Path):
    with with_env({'QEMU_DEV': str(tmp_path / 'qemu-dev' / 'qemu-some-file')}):
        p = do_find_qemu(tmp_path)
        assert p == tmp_path / 'qemu-dev' / 'qemu-some-file'


def test_precedence(tmp_path: Path):
    qemu_dir = tmp_path / 'qemu-dir'
    path1 = tmp_path / 'path' / 'dir1'
    path2 = tmp_path / 'path' / 'dir2'

    files = [
        # QEMU_DIR
        place_echo_args(qemu_dir / ENGINE),

        # Explicit search dir
        place_echo_args(tmp_path / 'my-qemu' / ENGINE),

        # Runner ancestors
        place_echo_args(tmp_path / 'runner' / 'dir1' / ENGINE),
        place_echo_args(tmp_path / 'runner' / 'dir1' / 'qemu' / ENGINE),
        place_echo_args(tmp_path / 'runner' / ENGINE),
        place_echo_args(tmp_path / 'runner' / 'qemu' / ENGINE),

        # PATH
        place_echo_args(path1 / ENGINE),
        place_echo_args(path2 / ENGINE),
    ]

    while len(files) > 0:
        with with_env({
            'QEMU_DIR': str(qemu_dir),
            'PATH': os.pathsep.join([str(path1), str(path2)]),
        }):
            p = find_qemu(
                ENGINE,
                [str(tmp_path / 'runner' / 'dir1' / 'check.py')],
                search_paths=[str(tmp_path / 'my-qemu')]
            )

            assert p == Path(files[0])

        os.unlink(files[0])
        del files[0]
