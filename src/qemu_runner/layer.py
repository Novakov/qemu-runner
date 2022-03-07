from configparser import ConfigParser
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Sequence, Dict, Protocol, Optional, Iterable

from .argument import Argument, ArgumentValue, build_command_line_for_argument


@dataclass(frozen=True)
class GeneralSettings:
    engine: str = ''
    kernel: Optional[str] = None
    kernel_cmdline: Optional[str] = None
    halted: Optional[bool] = None
    gdb: Optional[bool] = None
    gdb_dev: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[str] = None


class Layer:
    def __init__(self, general: GeneralSettings = GeneralSettings(), arguments: Sequence[Argument] = ()):
        self._general = general
        self._arguments: List[Argument] = list(arguments)

    @property
    def general(self) -> GeneralSettings:
        return self._general

    @property
    def arguments(self) -> Sequence[Argument]:
        return self._arguments

    def apply(self, addition: 'Layer') -> 'Layer':
        def apply_general() -> GeneralSettings:
            other = addition._general
            return replace(
                self._general,
                engine=other.engine if other.engine != '' else self._general.engine,
                kernel=other.kernel if other.kernel != '' else self._general.kernel,
                kernel_cmdline=other.kernel_cmdline if other.kernel_cmdline != '' else self._general.kernel_cmdline,
                halted=other.halted if other.halted is not None else self._general.halted,
                gdb=other.gdb if other.gdb is not None else self._general.gdb,
                gdb_dev=other.gdb_dev if other.gdb_dev is not None else self._general.gdb_dev,
            )

        def apply_arguments() -> Iterable[Argument]:
            remaining_other = list(addition._arguments)

            for arg in self._arguments:
                arg_addition = [other_arg for other_arg in remaining_other if other_arg.id_matches(arg)]

                assert len(arg_addition) <= 1

                if len(arg_addition) == 0:
                    yield arg
                else:
                    updated_arg = arg.update_arguments(arg_addition[0].attributes)
                    if arg_addition[0].value is not None:
                        updated_arg = updated_arg.replace_value(arg_addition[0].value)
                    yield updated_arg
                    remaining_other.remove(arg_addition[0])

            for arg in remaining_other:
                yield arg

        return Layer(
            general=apply_general(),
            arguments=list(apply_arguments())
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Layer):
            return False

        if self._general != other._general:
            return False

        if len(self._arguments) != len(other._arguments):
            return False

        for a in self._arguments:
            if a not in other._arguments:
                return False

        return True

    def __repr__(self):
        return f'Layer(general={self._general!r}, arguments={self._arguments!r})'


WELL_KNOWN_SECTIONS = ['general']
WELL_KNOWN_ARGUMENT_ATTRIBUTES = ['@']


def parse_layer(config_parser: ConfigParser) -> Layer:
    def read_argument_attributes(section: str) -> Dict[str, ArgumentValue]:
        result = {k: v for k, v in config_parser.items(section) if k not in WELL_KNOWN_ARGUMENT_ATTRIBUTES}

        if ':' in section:
            _, arg_id = section.split(':', maxsplit=1)
            result['id'] = arg_id

        return result

    def read_argument(section: str) -> Argument:
        if ':' in section:
            arg_name, _ = section.split(':', maxsplit=1)
        else:
            arg_name = section

        return Argument(
            name=arg_name,
            value=config_parser.get(section, '@', fallback=None),
            attributes=read_argument_attributes(section)
        )

    def read_arguments() -> List[Argument]:
        return [read_argument(section) for section in config_parser.sections() if section not in WELL_KNOWN_SECTIONS]

    def read_general_settings() -> GeneralSettings:
        result = GeneralSettings()

        if not config_parser.has_section('general'):
            return result

        section = dict(config_parser.items('general'))

        if 'engine' in section:
            result = replace(result, engine=section['engine'])

        if 'kernel' in section:
            result = replace(result, kernel=section['kernel'])

        if 'cmdline' in section:
            result = replace(result, kernel_cmdline=section['cmdline'])

        if 'gdb' in section:
            result = replace(result, gdb=config_parser.getboolean('general', 'gdb'))

        if 'gdb_dev' in section:
            result = replace(result, gdb_dev=section['gdb_dev'])

        if 'halted' in section:
            result = replace(result, halted=config_parser.getboolean('general', 'halted'))

        return result

    return Layer(
        general=read_general_settings(),
        arguments=read_arguments()
    )


class FindQemuFunc(Protocol):
    def __call__(self, engine: str) -> Path:
        pass


def build_command_line(layer: Layer, find_qemu_func: Optional[FindQemuFunc] = None) -> Sequence[str]:
    if layer.general.engine == '':
        raise Exception('Must specify engine')

    def _yield_args():
        if find_qemu_func:
            yield str(find_qemu_func(layer.general.engine))
        else:
            yield layer.general.engine

        for arg in layer.arguments:
            yield from build_command_line_for_argument(arg)

        if layer.general.cpu:
            yield '-cpu'
            yield layer.general.cpu

        if layer.general.memory:
            yield '-m'
            yield layer.general.memory

        if layer.general.halted:
            yield '-S'

        if layer.general.gdb:
            if layer.general.gdb_dev:
                yield '-gdb'
                yield layer.general.gdb_dev
            else:
                yield '-s'

        if layer.general.kernel:
            yield '-kernel'
            yield layer.general.kernel

        if layer.general.kernel_cmdline:
            yield '-append'
            yield layer.general.kernel_cmdline

    return list(_yield_args())
