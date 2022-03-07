import os
import subprocess
import venv
from pathlib import Path
from threading import Thread
from typing import List
from urllib.parse import urlparse
from urllib.request import urlretrieve

import pytest

from tests.test_utllities import with_env, place_echo_args


def install_script(builder: venv.EnvBuilder, context, name, url):
    _, _, path, _, _, _ = urlparse(url)
    fn = os.path.split(path)[-1]
    binpath = context.bin_path
    distpath = os.path.join(binpath, fn)
    # Download script into the virtual environment's binaries folder
    urlretrieve(url, distpath)
    # Install in the virtual environment
    args = [context.env_exe, fn]
    p = subprocess.Popen(args, cwd=binpath)
    p.wait()
    # Clean up - no longer needed
    os.unlink(distpath)


def install_setuptools(builder: venv.EnvBuilder, context):
    """
    Install setuptools in the virtual environment.

    :param context: The information for the virtual environment
                    creation request being processed.
    """
    url = 'https://bitbucket.org/pypa/setuptools/downloads/ez_setup.py'
    install_script(builder, context, 'setuptools', url)
    # clear up the setuptools archive which gets downloaded
    pred = lambda o: o.startswith('setuptools-') and o.endswith('.tar.gz')
    files = filter(pred, os.listdir(context.bin_path))
    for f in files:
        f = os.path.join(context.bin_path, f)
        os.unlink(f)


@pytest.fixture()
def venv_py(tmp_path: Path) -> Path:
    venv_dir = tmp_path / 'venv'
    return create_venv(venv_dir)


def create_venv(venv_dir: Path):
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(venv_dir)
    ctx = builder.ensure_directories(venv_dir)
    # builder.create_configuration(ctx)
    # builder.setup_python(ctx)
    # install_setuptools(builder, ctx)
    return Path(ctx.env_exe)


def make_runner(python: Path, args: List[str], cwd: Path):
    cp = subprocess.run([
        python,
        '-m', 'qemu_runner.make_runner',
        *args
    ],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8'
    )

    assert cp.stderr == ''
    assert cp.returncode == 0


def install_dev_package(python: Path, pkg: Path):
    cp = subprocess.run([
        python,
        pkg / 'setup.py',
        '-q',
        'install'
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',
        cwd=pkg
    )

    assert cp.returncode == 0, 'Package install error: ' + cp.stderr


def test_with_venv(tmp_path: Path, venv_py: Path):
    install_dev_package(venv_py, Path(__file__).parent / 'test_packages' / 'pkg1')

    with with_env({'PYTHONPATH': Path(__file__).parent.parent / 'src'}):
        layers = ['virt-cortex-m.ini', 'test.ini']
        make_runner(venv_py, ['--layers', *layers, '--output', 'runner.pyz'], cwd=tmp_path)


def test_with_multiple_venvs(tmp_path: Path):
    venv1 = create_venv(tmp_path / 'venv1')
    venv2 = create_venv(tmp_path / 'venv2')
    venv3 = create_venv(tmp_path / 'venv3')

    with with_env({'PYTHONPATH': Path(__file__).parent.parent / 'src'}):
        layers = ['virt-cortex-m.ini']
        make_runner(venv1, ['--layers', *layers, '--output', tmp_path / 'base_runner.pyz'], cwd=tmp_path)

    install_dev_package(venv2, Path(__file__).parent / 'test_packages' / 'pkg1')

    cp = subprocess.run([
        venv2,
        str(tmp_path / 'base_runner.pyz'),
        '--layers', 'test.ini',
        '--derive', str(tmp_path / 'derived.pyz'),
    ])

    assert cp.returncode == 0

    place_echo_args(tmp_path / 'qemu' / 'qemu-system-arm')

    cp = subprocess.run([
        venv3,
        str(tmp_path / 'derived.pyz'),
        'kernel.elf',
        'a', 'b', 'c'
    ])

    assert cp.returncode == 0