import argparse
import configparser
import os
from dataclasses import dataclass, field
from os.path import dirname
from typing import Union, Dict, Optional, Callable, Type, Any, TextIO

ArgValue = Union[str, int, None, 'ProvidedValue']


@dataclass(frozen=True)
class Argument:
    name: str
    value: Union[str, None] = None
    arguments: Dict[str, ArgValue] = field(default_factory=lambda: {})


@dataclass(frozen=True)
class ProvidedValue:
    name: str
    default: ArgValue
    cast_to: Type = str
    translate: Optional[Callable[[str], ArgValue]] = None


def build_argument_command_line(argument: Argument) -> list[str]:
    values = []

    if argument.value:
        values.append(argument.value)

    for k, v in argument.arguments.items():
        values.append(f'{k}={v}')

    result = [
        f'-{argument.name}',
    ]

    if any(values):
        result.append(','.join(values))

    return result


def find_qemu(engine: str) -> str:
    def find_executable(base_path: str) -> Optional[str]:
        exts = os.environ.get('PATHEXT', '').split(os.path.pathsep)
        for e in exts:
            path = f'{base_path}/{engine}{e}'
            if os.path.exists(path):
                return path
        return None

    paths_to_check = []

    # TODO: os.environ['QEMU_DEV']

    if 'QEMU_DIR' in os.environ:
        paths_to_check.append(os.environ['QEMU_DIR'].rstrip('/').rstrip('\\'))

    look_at = dirname(__file__)
    while True:
        paths_to_check.append(look_at)
        paths_to_check.append(look_at + '/qemu')
        look_at_next = dirname(look_at)
        if look_at_next == look_at:
            break

        look_at = look_at_next

    paths_to_check.extend(os.environ.get('PATH', '').split(os.pathsep))

    for p in paths_to_check:
        found = find_executable(p)
        if found is not None:
            return found

    return engine


def build_command_line(something: Any) -> list[str]:
    result = []

    result.append(find_qemu(something['engine']))

    arguments: list[Argument] = something['opts']

    for arg in arguments:
        result.extend(build_argument_command_line(arg))

    return result


def load_base_def_from_layers(layers: list[Union[os.PathLike, TextIO]]) -> Any:
    result = {
        'engine': '',
        'opts': []
    }

    qemu_args: list[Argument] = result['opts']

    for layer_path in layers:
        layer = configparser.ConfigParser()

        if isinstance(layer_path, os.PathLike):
            with open(layer_path, 'r') as f:
                layer.read_file(f)
        else:
            layer.read_file(layer_path)

        if layer.get('general', 'engine', fallback=None):
            result['engine'] = layer['general']['engine']

        for section in layer.sections():
            if section in ['general']:
                continue

            [argument_name, *id_values] = section.split(':', maxsplit=1)

            if len(id_values) >= 1:
                id_value = id_values[0]
            else:
                id_value = None

            matching_opts = [
                o
                for o in qemu_args
                if o.name == argument_name and (id_value is None or o.arguments.get('id', None) == id_value)
            ]
            if len(matching_opts) == 1:
                existing: Argument = matching_opts[0]
                idx = qemu_args.index(existing)

                qemu_args.remove(existing)
                args = dict(existing.arguments)
                args.update({
                    k: layer.get(section, k) for k in layer.options(section) if k not in ['@']
                })

                argument = Argument(
                    name=argument_name,
                    value=layer.get(section, '@', fallback=existing.value),
                    arguments=args
                )

                qemu_args.insert(idx, argument)
            elif len(matching_opts) > 1:
                raise ValueError(f'More than one matching arg for {section}')
            else:
                args = {
                    k: layer.get(section, k) for k in layer.options(section) if k not in ['@']
                }
                if id_value:
                    args['id'] = id_value

                argument = Argument(
                    name=argument_name,
                    value=layer.get(section, '@', fallback=None),
                    arguments=args
                )
                qemu_args.append(argument)

    return result


def make_arg_parser(base_definition: Any) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    args: list[Argument] = base_definition['opts']

    for arg in args:
        # TODO: if isinstance(arg.value, ProvidedValue):
        for k, v in arg.arguments.items():
            if isinstance(v, ProvidedValue):
                parser.add_argument(f'--{v.name}', default=v.default, dest=v.name, type=v.cast_to)

    parser.add_argument('kernel')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    return parser


def build_full_def(base_definition: Any, args: argparse.Namespace) -> Any:
    result = {**base_definition}

    qemu_args: list[Argument] = base_definition['opts']

    for arg in qemu_args:
        # TODO: if isinstance(arg.value, ProvidedValue):
        for k, v in arg.arguments.items():
            if isinstance(v, ProvidedValue):
                replacement_value = args.__dict__[v.name]
                if v.translate:
                    replacement_value = v.translate(replacement_value)
                arg.arguments[k] = replacement_value

    result['opts'].extend([
        Argument('kernel', value=args.kernel),
        Argument('append', value=' '.join(args.arguments))
    ])

    return result
