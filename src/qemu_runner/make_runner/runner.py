import subprocess
import sys
from io import StringIO

from qemu_runner import load_base_def_from_layers, make_arg_parser, build_full_def, build_command_line
from qemu_runner.layer import load_layer


def build_qemu_command_line(embdedded_layers: list[str], args: list[str]) -> list[str]:
    layer_contents = [StringIO(load_layer(
        layer,
        packages=['embedded_layers']
    )) for layer in embdedded_layers]
    base_def = load_base_def_from_layers(layer_contents)
    arg_parser = make_arg_parser(base_def)
    args = arg_parser.parse_args(args)
    full_def = build_full_def(base_def, args)
    full_cmdline = build_command_line(full_def)
    return full_cmdline


def execute_process(command_line: list[str]) -> None:
    cp = subprocess.run(command_line)
    sys.exit(cp.returncode)
