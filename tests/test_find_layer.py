import os
from contextlib import ExitStack
from pathlib import Path

import pytest

from qemu_runner.layer_locator import load_layer, LayerNotFoundError
from tests.test_utllities import with_cwd, place_file, with_env, with_pypath, unload_module_on_exit


def test_find_layer_file(tmp_path: Path):
    place_file(tmp_path / 'layer-test.ini', 'file-layer')

    with with_cwd(tmp_path):
        content = load_layer(
            'layer-test.ini',
            packages=[],
            search_dir=[],
            environ_names=[]
        )

        assert content == 'file-layer'


def test_find_layer_file_abs_path(tmp_path: Path):
    place_file(tmp_path / 'layer-test.ini', 'file-layer')

    with with_cwd(tmp_path):
        content = load_layer(
            str(tmp_path / 'layer-test.ini'),
            packages=[],
            search_dir=[],
            environ_names=[]
        )

        assert content == 'file-layer'


def test_find_layer_search_dir(tmp_path: Path):
    place_file(tmp_path / 'layer1' / 'layer-test.ini', 'file-layer')

    with with_cwd(tmp_path):
        content = load_layer(
            'layer-test.ini',
            packages=[],
            search_dir=[tmp_path / 'layer1'],
            environ_names=[]
        )

        assert content == 'file-layer'


def test_find_layer_env_dir(tmp_path: Path):
    place_file(tmp_path / 'layer1' / 'layer-test.ini', 'file-layer')

    with with_cwd(tmp_path), with_env({'QEMU_RUNNER_LAYERS': tmp_path / 'layer1'}):
        content = load_layer(
            'layer-test.ini',
            packages=[],
            search_dir=[],
            environ_names=['QEMU_RUNNER_LAYERS']
        )

        assert content == 'file-layer'


def test_find_layer_package(tmp_path: Path):
    place_file(tmp_path / 'py-path' / 'layer1' / '__init__.py', '')
    place_file(tmp_path / 'py-path' / 'layer1' / 'layers' / 'layer-test.ini', 'file-layer')

    with with_cwd(tmp_path), with_pypath(tmp_path / 'py-path'), unload_module_on_exit('layer1'):
        content = load_layer(
            'layer-test.ini',
            packages=['layer1'],
            search_dir=[],
            environ_names=[]
        )

        assert content == 'file-layer'


def test_find_layer_package_subdir(tmp_path: Path):
    place_file(tmp_path / 'py-path' / 'layer1' / '__init__.py', '')
    place_file(tmp_path / 'py-path' / 'layer1' / 'layers' / 'sub' / 'layer-test.ini', 'file-layer')

    with with_cwd(tmp_path), with_pypath(tmp_path / 'py-path'), unload_module_on_exit('layer1'):
        content = load_layer(
            'sub/layer-test.ini',
            packages=['layer1'],
            search_dir=[],
            environ_names=[]
        )

        assert content == 'file-layer'


def test_find_layer_package_gracefully_handle_no_file(tmp_path: Path):
    place_file(tmp_path / 'py-path' / 'layer1' / '__init__.py', '')
    place_file(tmp_path / 'py-path' / 'layer1' / 'layers' / 'layer-test.ini', 'file-layer')

    with with_cwd(tmp_path), with_pypath(tmp_path / 'py-path'), unload_module_on_exit('layer1'):
        with pytest.raises(LayerNotFoundError):
            load_layer(
                'layer-test2.ini',
                packages=['layer1'],
                search_dir=[],
                environ_names=[]
            )


def test_precedence(tmp_path):
    place_file(tmp_path / 'py-path' / 'layer1' / '__init__.py', '')
    place_file(tmp_path / 'py-path' / 'layer2' / '__init__.py', '')

    files = [
        tmp_path / 'layer-test.ini',
        tmp_path / 'search-dir1' / 'layer-test.ini',
        tmp_path / 'search-dir2' / 'layer-test.ini',
        tmp_path / 'env-dir1a' / 'layer-test.ini',
        tmp_path / 'env-dir1b' / 'layer-test.ini',
        tmp_path / 'env-dir2a' / 'layer-test.ini',
        tmp_path / 'env-dir2b' / 'layer-test.ini',
        tmp_path / 'py-path' / 'layer1' / 'layers' / 'layer-test.ini',
        tmp_path / 'py-path' / 'layer2' / 'layers' / 'layer-test.ini',
    ]

    for f in files:
        place_file(f, str(f))

    with ExitStack() as stack:
        stack.enter_context(with_pypath(tmp_path / 'py-path'))
        stack.enter_context(with_cwd(tmp_path))
        stack.enter_context(with_env({
            'DIR1': os.pathsep.join([str(tmp_path / 'env-dir1a'), str(tmp_path / 'env-dir1b')]),
            'DIR2': os.pathsep.join([str(tmp_path / 'env-dir2a'), str(tmp_path / 'env-dir2b')]),
        }))
        stack.enter_context(unload_module_on_exit('layer1', 'layer2'))

        while len(files) > 0:
            expected = files[0]

            content = load_layer(
                'layer-test.ini',
                packages=['layer1', 'layer2'],
                search_dir=[tmp_path / 'search-dir1', tmp_path / 'search-dir2'],
                environ_names=['DIR1', 'DIR2']
            )

            assert content == str(expected)

            os.unlink(expected)
            del files[0]

