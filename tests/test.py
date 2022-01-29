import argparse
import configparser
import os.path
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union, Dict, Optional, Callable, Type

from qemu_runner import *


def test_simulate_wrapper_call() -> None:
    base_def = {
        'engine': 'qemu-system-arm',
        'opts': [
            Argument(
                name='machine',
                value='virt-cortex-m',
                arguments={'flash_kb': 1024, }
            ),
            Argument(name='device', value='kp-edi-group', arguments={'count': 20}),
            Argument(name='device', value='kp-posix'),
            Argument(name='semihosting'),
            Argument(name='semihosting-config', arguments={'target': 'native'})
        ]
    }

    arg_parser = make_arg_parser(base_def)
    parsed_args, _ = arg_parser.parse_known_args(['/path/to/kernel', 'arg1', 'arg2', 'arg3'])

    full_def = build_full_def(base_def, parsed_args)
    full_cmdline = build_command_line(full_def)

    assert full_cmdline == [
        'qemu-system-arm',
        '-machine', 'virt-cortex-m,flash_kb=1024',
        '-device', 'kp-edi-group,count=20',
        '-device', 'kp-posix',
        '-semihosting',
        '-semihosting-config', 'target=native',
        '-kernel', '/path/to/kernel',
        '-append', 'arg1 arg2 arg3',
    ]


def test_simulate_wrapper_call_dashes() -> None:
    base_def = {
        'engine': 'qemu-system-arm',
        'opts': [
            Argument(
                name='machine',
                value='virt-cortex-m',
                arguments={'flash_kb': 1024, }
            ),
            Argument(name='device', value='kp-edi-group', arguments={'count': 20}),
            Argument(name='device', value='kp-posix'),
            Argument(name='semihosting'),
            Argument(name='semihosting-config', arguments={'target': 'native'})
        ]
    }

    arg_parser = make_arg_parser(base_def)
    parsed_args, _ = arg_parser.parse_known_args(['/path/to/kernel', 'arg1', 'arg2', '--help'])

    full_def = build_full_def(base_def, parsed_args)
    full_cmdline = build_command_line(full_def)

    assert full_cmdline == [
        'qemu-system-arm',
        '-machine', 'virt-cortex-m,flash_kb=1024',
        '-device', 'kp-edi-group,count=20',
        '-device', 'kp-posix',
        '-semihosting',
        '-semihosting-config', 'target=native',
        '-kernel', '/path/to/kernel',
        '-append', 'arg1 arg2 --help',
    ]


def test_parametrize_edi_count() -> None:
    base_def = {
        'engine': 'qemu-system-arm',
        'opts': [
            Argument(
                name='machine',
                value='virt-cortex-m',
                arguments={'flash_kb': 1024, }
            ),
            Argument(
                name='device',
                value='kp-edi-group',
                arguments={
                    'count': ProvidedValue('edi-count', 20)
                }
            ),
            Argument(name='device', value='kp-posix'),
            Argument(name='semihosting'),
            Argument(name='semihosting-config', arguments={'target': 'native'})
        ]
    }

    arg_parser = make_arg_parser(base_def)
    parsed_args, _ = arg_parser.parse_known_args(['--edi-count=20', '/path/to/kernel', 'arg1', 'arg2', '--help'])

    full_def = build_full_def(base_def, parsed_args)
    full_cmdline = build_command_line(full_def)

    assert full_cmdline == [
        'qemu-system-arm',
        '-machine', 'virt-cortex-m,flash_kb=1024',
        '-device', 'kp-edi-group,count=20',
        '-device', 'kp-posix',
        '-semihosting',
        '-semihosting-config', 'target=native',
        '-kernel', '/path/to/kernel',
        '-append', 'arg1 arg2 --help',
    ]


def test_parametrize_edi_base_translate_to_hex() -> None:
    base_def = {
        'engine': 'qemu-system-arm',
        'opts': [
            Argument(
                name='machine',
                value='virt-cortex-m',
                arguments={'flash_kb': 1024, }
            ),
            Argument(
                name='device',
                value='kp-edi-group',
                arguments={
                    'addr': ProvidedValue('edi-base', 20, cast_to=int, translate=lambda x: f'0x{x:08X}')
                }
            ),
            Argument(name='device', value='kp-posix'),
            Argument(name='semihosting'),
            Argument(name='semihosting-config', arguments={'target': 'native'})
        ]
    }

    arg_parser = make_arg_parser(base_def)
    parsed_args, _ = arg_parser.parse_known_args(['--edi-base=4026531856', '/path/to/kernel', 'arg1', 'arg2', '--help'])

    full_def = build_full_def(base_def, parsed_args)
    full_cmdline = build_command_line(full_def)

    assert full_cmdline == [
        'qemu-system-arm',
        '-machine', 'virt-cortex-m,flash_kb=1024',
        '-device', 'kp-edi-group,addr=0xF0000010',
        '-device', 'kp-posix',
        '-semihosting',
        '-semihosting-config', 'target=native',
        '-kernel', '/path/to/kernel',
        '-append', 'arg1 arg2 --help',
    ]


def test_construct_commandline_from_layers() -> None:
    base_dir = Path(os.path.dirname(__file__)) / 'layers'
    base_def = load_base_def_from_layers([
        base_dir / 'virt-cortex-m.ini',
        base_dir / 'edi.ini',
        base_dir / 'semihosting.ini'
    ])

    arg_parser = make_arg_parser(base_def)
    parsed_args, _ = arg_parser.parse_known_args(['/path/to/kernel', 'arg1', 'arg2', '--help'])

    full_def = build_full_def(base_def, parsed_args)
    full_cmdline = build_command_line(full_def)

    assert full_cmdline == [
        'qemu-system-arm',
        '-machine', 'virt-cortex-m,flash_kb=1024',
        '-device', 'kp-edi-group,id=edi',
        '-semihosting',
        '-semihosting-config', 'target=native',
        '-kernel', '/path/to/kernel',
        '-append', 'arg1 arg2 --help',
    ]


def test_construct_commandline_from_layers_modify_edi_count() -> None:
    base_dir = Path(os.path.dirname(__file__)) / 'layers'
    base_def = load_base_def_from_layers([
        base_dir / 'virt-cortex-m.ini',
        base_dir / 'edi.ini',
        base_dir / 'edi-count.ini',
        base_dir / 'semihosting.ini'
    ])

    arg_parser = make_arg_parser(base_def)
    parsed_args, _ = arg_parser.parse_known_args(['/path/to/kernel', 'arg1', 'arg2', '--help'])

    full_def = build_full_def(base_def, parsed_args)
    full_cmdline = build_command_line(full_def)

    assert full_cmdline == [
        'qemu-system-arm',
        '-machine', 'virt-cortex-m,flash_kb=1024',
        '-device', 'kp-edi-group,id=edi,count=30',
        '-semihosting',
        '-semihosting-config', 'target=native',
        '-kernel', '/path/to/kernel',
        '-append', 'arg1 arg2 --help',
    ]


def test_build_command_line():
    cmdline = build_command_line({
        'engine': 'qemu-system-arm',
        'opts': [
            Argument(
                name='machine',
                value='virt-cortex-m',
                arguments={'flash_kb': 1024, }
            ),
            Argument(name='kernel', value='/path/to/kernel'),
            Argument(name='append', value=' '.join(['arg1', 'arg2', 'arg3'])),
            Argument(name='device', value='kp-edi-group', arguments={'count': 20}),
            Argument(name='device', value='kp-posix'),
            Argument(name='semihosting'),
            Argument(name='semihosting-config', arguments={'target': 'native'})
        ]
    })

    assert cmdline == [
        'qemu-system-arm',
        '-machine', 'virt-cortex-m,flash_kb=1024',
        '-kernel', '/path/to/kernel',
        '-append', 'arg1 arg2 arg3',
        '-device', 'kp-edi-group,count=20',
        '-device', 'kp-posix',
        '-semihosting',
        '-semihosting-config', 'target=native'
    ]

# Jakoś działa
# Mam konwersję model -> command line
# Model jest bardzo ogólny
# Proste użycie ProvidedValue w modelu daje możliwośc określenia 'tu wartość od usera'
# Generowanie ArgumentParsera jest bardzo proste, jego użycie też
# Problem: Zapakowanie tego w realnie używalny skrypt/zipapp
# Problem: ścieżka do qemu
#   Dobrze by było gdyby potrafiło samo znaleźć
#   Ale też override jakaś opcja byłby przydatny:
#       environ['QEMU_DEV'] -> --qemu -> environ['QEMU_DIR']/<kind> -> dirname(__file__)/<kind>
# Problem: Definiowanie bazowego modelu
# Problem: Overlaye/layery modelu
#   Chciałbym mieć możliwość uzupełnienia wartości np. device'a w wcześniej zdefiniowanych opcjach
#   Można podawać `id` dla device'a/chardeva
#   Wychodzi więc, ze w layerach wyżej można by dopasowywać `typ:id` jako unikalny klucz i w ten sposób mergować opcje
#   QOM jest sprytny ;)

# TODO: py -m qemu_runner.make -s <spec1> <spec2> <spec3> runner.pyz && ./runner.pyz kernel.elf arg1 arg2 arg3
