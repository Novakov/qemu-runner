import argparse
import subprocess
import sys
from configparser import ConfigParser

from qemu_runner import find_qemu
from qemu_runner.layer import Layer, parse_layer, build_command_line, GeneralSettings
from qemu_runner.layer_locator import load_layer


def make_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--halted', action='store_true', help='Halt machine on startup')
    parser.add_argument('--debug', action='store_true', help='Enable QEMU gdbserver')
    parser.add_argument('--debug-listen', help='QEMU gdbserver listen address')

    parser.add_argument('kernel')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    return parser


def make_layer_from_args(args: argparse.Namespace) -> Layer:
    general = GeneralSettings(
        kernel=args.kernel,
        kernel_cmdline=' '.join(args.arguments),
        gdb=args.debug,
        gdb_dev=args.debug_listen,
        halted=args.halted,
    )
    return Layer(general=general)


def build_qemu_command_line(embdedded_layers: list[str], args: list[str]) -> list[str]:
    layer_contents = [load_layer(
        layer,
        packages=['embedded_layers']
    ) for layer in embdedded_layers]

    combined_layer = Layer()

    for layer_content in layer_contents:
        parser = ConfigParser()
        parser.read_string(layer_content)
        layer = parse_layer(parser)
        combined_layer = combined_layer.apply(layer)

    arg_parser = make_arg_parser()
    parsed_args = arg_parser.parse_args(args)

    args_layer = make_layer_from_args(parsed_args)

    combined_layer = combined_layer.apply(args_layer)

    full_cmdline = build_command_line(combined_layer, find_qemu_func=find_qemu)

    return list(full_cmdline)


def execute_process(command_line: list[str]) -> None:
    cp = subprocess.run(command_line)
    sys.exit(cp.returncode)
