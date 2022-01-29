import argparse
import pkgutil
import shutil
import zipfile
from importlib import resources
from importlib.abc import Traversable
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--layers', nargs='+', required=True, help='Layer files')
    parser.add_argument('-o', '--output', required=True, help='Output .pyz file', type=argparse.FileType('wb'))
    return parser.parse_args()


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


def main(args: argparse.Namespace):
    with zipfile.ZipFile(args.output, mode='w') as archive:
        copy_directory(resources.files('qemu_runner'), archive, Path('qemu_runner'))
        with archive.open('__main__.py', 'w') as f:
            main_template = pkgutil.get_data('qemu_runner.make_runner', 'main.py.in').decode('utf-8')
            f.write(main_template.format(
                layers=args.layers
            ).encode('utf-8'))


if __name__ == '__main__':
    main(parse_args())
