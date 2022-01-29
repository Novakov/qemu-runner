import importlib.resources
import pkgutil
from importlib.abc import Traversable
from io import StringIO

from qemu_runner import *

layers = [
    'virt-cortex-m.ini'
]


def traverse(t: Traversable, indent: str = ''):
    for item in t.iterdir():
        print(indent + str(item))
        if item.is_dir():
            traverse(item, indent + '    ')


def main():
    print('Hello')

    # traverse(importlib.resources.files('qemu_runner'))

    base_def = load_base_def_from_layers([
        StringIO(pkgutil.get_data('qemu_runner', 'layers/' + layer).decode('utf-8')) for layer in layers
    ])

    arg_parser = make_arg_parser(base_def)

    args = arg_parser.parse_args()

    full_def = build_full_def(base_def, args)
    full_cmdline = build_command_line(full_def)
    print(full_cmdline)
