import argparse
import os
import shlex
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import List, Optional


def make_path_absolute(v: str) -> str:
    return os.path.abspath(v)

def make_arg_parser():
    parser = argparse.ArgumentParser()
    parser.formatter_class = argparse.RawDescriptionHelpFormatter

    parser.description = '''QEMU runner wraps series of layers describing QEMU arguments as standalone executable file (ZIP file actually)
requiring only Python 3.8+ standard library. 
'''

    qemu_dev = os.environ.get('QEMU_DEV', '<not set>')
    qemu_dir = os.environ.get('QEMU_DIR', '<not set>')
    qemu_runner_flags = os.environ.get('QEMU_RUNNER_FLAGS', '<not set>')
    qemu_flags = os.environ.get('QEMU_FLAGS', '<not set>')

    parser.epilog = f'''
QEMU search precedence:
    1. QEMU_DEV environment variable, direct path to executable (currently: {qemu_dev})
    2. --qemu argument as direct path to executable (if specified)
    3. QEMU_DIR environment variable, path to directory containing QEMU executable (currently: {qemu_dir})
    4. --qemu-dir argument (if specified)
    5. Runner and it's ancestor directories and /qemu subdirectory on each level
    6. The same rule as (3) but for paths of base runners when derived with --track-qemu flag
    7. The same rule as (3) but for paths added with --qemu-dir when derived
    8. Directories in PATH environment variable
    
Runtime QEMU flags
    1. Contents of QEMU_RUNNER_FLAGS (currently: {qemu_runner_flags}) are treated as runner arguments
    2. Contents of QEMU_FLAGS (currently: {qemu_flags}) are added as QEMU arguments without any interpretation 
'''

    runner_args = parser.add_argument_group('Runner arguments')
    runner_args.add_argument('--qemu-dir', help='Directory where runner should look for QEMU engine.')
    runner_args.add_argument('--qemu', help='Explicit path to QEMU executable')
    runner_args.add_argument('--inspect', help='Inspect content of runner archive', action='store_true')
    runner_args.add_argument('--derive', help='Create new runner based on current one', type=argparse.FileType('wb'))

    derive_args = parser.add_argument_group('Deriving runner with --derive')
    derive_args.add_argument('--layers', nargs='+', default=[])
    derive_args.add_argument('--track-qemu', action='store_true',
                             help='Add QEMU directory as visible by this runner to QEMU search path of derived runner')
    derive_args.description = '''Deriving runner allows to customize base runner (potentially provided externally) with
project-specific options. Additional options are specified as another set of layers that 
will be applied on top of layers embedded in base runner. Tracking QEMU with --track-qemu
allows to place derived runner in other directory (e.g. build directory of project) and 
still use QEMU search rules from base QEMU runner.  
'''

    qemu_args = parser.add_argument_group('QEMU arguments')
    qemu_args.add_argument('--halted', action='store_true', help='Halt machine on startup')
    qemu_args.add_argument('--debug', action='store_true', help='Enable QEMU gdbserver')
    qemu_args.add_argument('--debug-listen', help='QEMU gdbserver listen address', metavar='device')

    program_args = parser.add_argument_group('Program arguments')
    program_args.add_argument('--dry-run', action='store_true', help='Do not execute QEMU, just output command line')
    program_args.add_argument('kernel', help='Executable to run under QEMU', nargs='?', type=make_path_absolute)
    program_args.add_argument('arguments', nargs=argparse.REMAINDER, help='Arguments passed to executable', default=[])

    return parser


def make_layer_from_args(args: argparse.Namespace) -> 'Layer':
    from qemu_runner.layer import GeneralSettings, Layer
    general = GeneralSettings(
        kernel=args.kernel,
        kernel_cmdline=' '.join(args.arguments),
        gdb=args.debug,
        gdb_dev=args.debug_listen,
        halted=args.halted,
    )
    return Layer(general=general)


def build_qemu_command_line(
        *,
        embedded_layers: List[str],
        additional_script_bases: List[str],
        additional_search_paths: List[str],
        args: argparse.Namespace,
        additional_qemu_args: str) -> List[str]:
    from qemu_runner.layer_locator import load_layer
    layer_contents = [load_layer(
        layer,
        packages=['embedded_layers']
    ) for layer in embedded_layers]

    from qemu_runner.layer import Layer
    combined_layer = Layer()

    for layer_content in layer_contents:
        parser = ConfigParser()
        parser.read_string(layer_content)
        from qemu_runner.layer import parse_layer
        layer = parse_layer(parser)
        combined_layer = combined_layer.apply(layer)

    args_layer = make_layer_from_args(args)

    combined_layer = combined_layer.apply(args_layer)

    def do_find_qemu(engine: str) -> Optional[Path]:
        if args.qemu:
            return Path(args.qemu)

        from qemu_runner import find_qemu
        return find_qemu(
            engine=engine,
            script_paths=[__file__] + additional_script_bases,
            search_paths=additional_search_paths + ([args.qemu_dir] if args.qemu_dir else [])
        )

    from qemu_runner.layer import build_command_line
    full_cmdline = build_command_line(combined_layer, find_qemu_func=do_find_qemu)

    result = list(full_cmdline)

    if additional_qemu_args != '':
        user_qemu_args = shlex.split(additional_qemu_args, posix=sys.platform != 'win32')
        result = [result[0], *user_qemu_args, *result[1:]]

    return result


def execute_process(command_line: List[str]) -> None:
    try:
        cp = subprocess.run(command_line)
        sys.exit(cp.returncode)
    except FileNotFoundError:
        raise


def make_derived_runner(embedded_layers: List[str], additional_search_paths: List[str], args: argparse.Namespace) -> None:
    from qemu_runner.make_runner.make import make_runner, load_layers_from_all_search_paths
    from qemu_runner.layer_locator import load_layer
    base_layers = [load_layer(
        layer,
        packages=['embedded_layers']
    ) for layer in embedded_layers]

    additional_layers = load_layers_from_all_search_paths(args.layers)

    if args.track_qemu:
        base_script_paths: List[str] = [__file__]
    else:
        base_script_paths = []

    if args.qemu_dir:
        additional_search_paths.append(args.qemu_dir)

    make_runner(
        args.derive,
        layer_contents=base_layers + additional_layers,
        additional_script_bases=base_script_paths,
        additional_search_paths=additional_search_paths
    )


def make_layer_printer():
    try:
        from pygments import highlight
        from pygments.lexers.configs import IniLexer
        from pygments.formatters import TerminalFormatter
        lexer = IniLexer()
        formatter = TerminalFormatter()
        return lambda s: print(highlight(s, lexer, formatter).strip())
    except ImportError:
        return lambda s: print(s)


def inspect_runner(embedded_layers: List[str]) -> None:
    from qemu_runner.layer_locator import load_layer
    layers = [(layer, load_layer(
        layer,
        packages=['embedded_layers']
    )) for layer in embedded_layers]

    print_ini = make_layer_printer()

    for layer_name, layer in layers:
        print(f'# Layer embedded_layers/{layer_name}:')
        print_ini(layer.strip())
        print()


def execute_runner(embedded_layers: List[str], additional_script_bases: List[str], additional_search_paths: List[str], args: List[str]) -> None:
    arg_parser = make_arg_parser()

    env_runner_args = os.environ.get('QEMU_RUNNER_FLAGS', '')
    if env_runner_args != '':
        splitted_args = shlex.split(env_runner_args, posix=sys.platform != 'win32')
        args = [*splitted_args, *args]

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
        arg_parser.error('Specify action to perform: kernel, --derive or --inspect')

    if parsed_args.derive:
        make_derived_runner(embedded_layers, additional_search_paths, parsed_args)
    elif parsed_args.inspect:
        inspect_runner(embedded_layers)
    else:
        cmdline = build_qemu_command_line(
            embedded_layers=embedded_layers,
            additional_script_bases=additional_script_bases,
            additional_search_paths=additional_search_paths,
            args=parsed_args,
            additional_qemu_args=os.environ.get('QEMU_FLAGS', '')
        )

        if parsed_args.dry_run:
            print(shlex.join(cmdline))
            sys.exit(0)
        else:
            execute_process(cmdline)
