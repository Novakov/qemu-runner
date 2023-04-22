import importlib.resources
import os
import pkgutil
import shutil
import zipfile
import zipimport
from pathlib import Path
from typing import IO, List, Any
import pkg_resources

from qemu_runner.layer_locator import load_layer
import qemu_runner

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


if hasattr(importlib.resources, 'files'):
    def copy_directory_traversable(root: 'Traversable', archive: zipfile.ZipFile, subdir: Path) -> None:
        for item in root.iterdir():
            if item.name in ['__pycache__']:
                continue

            if item.is_file():
                with archive.open(str(subdir / item.name), 'w') as out_f:
                    with item.open('rb') as in_f:
                        shutil.copyfileobj(in_f, out_f)
            elif item.is_dir():
                copy_directory_traversable(item, archive, subdir / item.name)


def copy_directory_path(root: Path, archive: zipfile.ZipFile, archive_sub_dir: str) -> None:
    for sub_path_s, dir_names, file_names in os.walk(root):
        sub_path = Path(sub_path_s)

        if sub_path.name == '__pycache__':
            continue

        rel_path = sub_path.relative_to(root)

        for f in file_names:
            with archive.open(str(Path(archive_sub_dir) / rel_path / f), 'w') as out_f:
                with (sub_path / f).open('rb') as in_f:
                    shutil.copyfileobj(in_f, out_f)


def copy_directory_from_zip(archive_file: Path, source_sub_dir: Path, target_archive: zipfile.ZipFile, target_sub_dir: Path) -> None:
    with zipfile.ZipFile(archive_file, 'r') as source:
        for f in source.filelist:
            if f.is_dir():
                continue
            if Path(f.filename).parts[:len(source_sub_dir.parts)] != source_sub_dir.parts:
                continue

            rel_path = Path(f.filename).relative_to(source_sub_dir)

            with source.open(f, 'r') as in_f:
                with target_archive.open(str(target_sub_dir / rel_path), 'w') as out_f:
                    shutil.copyfileobj(in_f, out_f)


def copy_package(package: Any, archive: zipfile.ZipFile) -> None:
    if hasattr(importlib.resources, 'files'):
        from importlib import resources
        # Python 3.9+ has nice access to files in package using importlib.resources.file and Traversable
        copy_directory_traversable(resources.files(package), archive, Path(package.__name__))
    elif isinstance(package.__loader__, zipimport.zipimporter):
        # For older Python we need to treat packages from zip (runner) differently
        # zipimporter gives path to archive file, so we work how to open zip file
        # and extract package from it.
        # it's terrible
        source_dir = Path(package.__file__).parent.relative_to(package.__loader__.archive)
        copy_directory_from_zip(
            archive_file=Path(package.__loader__.archive),
            source_sub_dir=source_dir,
            target_archive=archive,
            target_sub_dir=Path(package.__name__)
        )
    else:
        # No Python 3.9, not zipimporter, let's hope that importlib.resources.path will do the job
        with importlib.resources.path(qemu_runner, '') as p:
            copy_directory_path(p, archive, package.__name__)


def make_runner(output: IO[bytes],
                *,
                layer_contents: List[str],
                additional_script_bases: List[str],
                additional_search_paths: List[str]
                ) -> None:
    with zipfile.ZipFile(output, mode='w', compression=zipfile.ZIP_STORED) as archive:
        copy_package(qemu_runner, archive)

        with archive.open('embedded_layers/__init__.py', 'w'):
            pass

        for i, layer_content in enumerate(layer_contents):
            with archive.open(f'embedded_layers/layers/{i}.ini', 'w') as f1:
                f1.write(layer_content.encode('utf-8'))

        with archive.open('__main__.py', 'w') as f:
            main_template = pkgutil.get_data('qemu_runner.make_runner', 'main.py.in').decode('utf-8')
            f.write(main_template.format(
                embedded_layers=[f'{i}.ini' for i in range(0, len(layer_contents))],
                additional_script_bases=additional_script_bases,
                additional_search_paths=additional_search_paths
            ).encode('utf-8'))
