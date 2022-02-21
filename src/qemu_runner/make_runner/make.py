import pkgutil
import shutil
import zipfile
from importlib import resources
from importlib.abc import Traversable
from pathlib import Path
from typing import IO, List
import pkg_resources

from qemu_runner.layer_locator import load_layer

__all__ = [
    'make_runner',
    'load_layers_from_all_search_paths',
]


def load_layers_from_all_search_paths(layer_names: List[str]) -> List[str]:
    packages = ['qemu_runner']
    for ep in pkg_resources.iter_entry_points('qemu_runner_layer_packages'):
        ep: pkg_resources.EntryPoint
        packages.append(ep.module_name)

    return [load_layer(layer, packages=packages) for layer in layer_names]


def copy_directory(root: Traversable, archive: zipfile.ZipFile, subdir: Path) -> None:
    for item in root.iterdir():
        if item.name in ['__pycache__']:
            continue

        if item.is_file():
            print(f'Copy {item} to {subdir}')
            with archive.open(str(subdir / item.name), 'w') as out_f:
                with item.open('rb') as in_f:
                    shutil.copyfileobj(in_f, out_f)
        elif item.is_dir():
            copy_directory(item, archive, subdir / item.name)


def make_runner(output: IO[bytes], layer_contents: List[str]) -> None:
    with zipfile.ZipFile(output, mode='w') as archive:
        copy_directory(resources.files('qemu_runner'), archive, Path('qemu_runner'))

        with archive.open('embedded_layers/__init__.py', 'w'):
            pass

        for i, layer_content in enumerate(layer_contents):
            with archive.open(f'embedded_layers/layers/{i}.ini', 'w') as f1:
                f1.write(layer_content.encode('utf-8'))

        with archive.open('__main__.py', 'w') as f:
            main_template = pkgutil.get_data('qemu_runner.make_runner', 'main.py.in').decode('utf-8')
            f.write(main_template.format(
                embedded_layers=[f'{i}.ini' for i in range(0, len(layer_contents))]
            ).encode('utf-8'))
