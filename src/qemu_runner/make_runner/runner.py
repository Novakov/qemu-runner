import argparse
import shlex
import subprocess
import sys
from configparser import ConfigParser

from qemu_runner import find_qemu
from qemu_runner.layer import Layer, parse_layer, build_command_line, GeneralSettings
from qemu_runner.layer_locator import load_layer
from qemu_runner.make_runner import make_runner


def make_arg_parser():
    parser = argparse.ArgumentParser()

    runner_args = parser.add_argument_group('Runner arguments')
    runner_args.add_argument('--inspect', help='Inspect content of runner archive', action='store_true')
    runner_args.add_argument('--derive', help='Create new runner based on current one', type=argparse.FileType('wb'))
    runner_args.add_argument('--layers', nargs='+', default=[])

    qemu_args = parser.add_argument_group('QEMU arguments')
    qemu_args.add_argument('--halted', action='store_true', help='Halt machine on startup')
    qemu_args.add_argument('--debug', action='store_true', help='Enable QEMU gdbserver')
    qemu_args.add_argument('--debug-listen', help='QEMU gdbserver listen address', metavar='device')

    program_args = parser.add_argument_group('Program arguments')
    program_args.add_argument('--dry-run', action='store_true', help='Do not execute QEMU, just output command line')
    program_args.add_argument('kernel', help='Executable to run under QEMU', nargs='?')
    program_args.add_argument('arguments', nargs=argparse.REMAINDER, help='Arguments passed to executable', default=[])

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


def build_qemu_command_line(embedded_layers: list[str], args: argparse.Namespace) -> list[str]:
    layer_contents = [load_layer(
        layer,
        packages=['embedded_layers']
    ) for layer in embedded_layers]

    combined_layer = Layer()

    for layer_content in layer_contents:
        parser = ConfigParser()
        parser.read_string(layer_content)
        layer = parse_layer(parser)
        combined_layer = combined_layer.apply(layer)

    args_layer = make_layer_from_args(args)

    combined_layer = combined_layer.apply(args_layer)

    full_cmdline = build_command_line(combined_layer, find_qemu_func=find_qemu)

    return list(full_cmdline)


def execute_process(command_line: list[str]) -> None:
    cp = subprocess.run(command_line)
    sys.exit(cp.returncode)


def make_derived_runner(embedded_layers: list[str], args: argparse.Namespace) -> None:
    base_layers = [load_layer(
        layer,
        packages=['embedded_layers']
    ) for layer in embedded_layers]

    additional_layers = [load_layer(
        layer,
        packages=['qemu_runner']
    ) for layer in args.layers]

    make_runner(args.derive, base_layers + additional_layers)


def execute_runner(embedded_layers: list[str], args: list[str]) -> None:
    arg_parser = make_arg_parser()
    parsed_args = arg_parser.parse_args(args)

    if parsed_args.derive and parsed_args.inspect:
        arg_parser.error('--derive and --inspect cannot be used together')

    if parsed_args.derive and parsed_args.kernel:
        arg_parser.error('--derive and kernel cannot be used together')

    if parsed_args.inspect and parsed_args.kernel:
        arg_parser.error('--inspect and kernel cannot be used together')

    if parsed_args.derive and parsed_args.dry_run:
        arg_parser.error('--derive and QEMU arguments cannot be used together')

    if parsed_args.inspect and parsed_args.dry_run:
        arg_parser.error('--derive and --dry-run cannot be used together')

    if not parsed_args.inspect and not parsed_args.derive and (not parsed_args.kernel and not parsed_args.dry_run):
        arg_parser.error('Specify action to perform: kernel, --dervice or --inspect')

    if parsed_args.derive:
        make_derived_runner(embedded_layers, parsed_args)
    else:
        cmdline = build_qemu_command_line(embedded_layers, parsed_args)

        if parsed_args.dry_run:
            print(shlex.join(cmdline))
            sys.exit(0)
        else:
            execute_process(cmdline)
