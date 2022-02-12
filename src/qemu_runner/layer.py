from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Dict, Protocol, Optional

from .argument import Argument, ArgumentValue, build_command_line_for_argument


@dataclass(frozen=True)
class GeneralSettings:
    engine: str = ''


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

    def apply(self, addition: 'Layer') -> 'Layer':
        pass  # TODO


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
            arguments=read_argument_attributes(section)
        )

    def read_arguments() -> List[Argument]:
        return [read_argument(section) for section in config_parser.sections() if section not in WELL_KNOWN_SECTIONS]

    def read_general_settings() -> GeneralSettings:
        return GeneralSettings(
            engine=config_parser.get('general', 'engine', fallback='')
        )

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
            yield find_qemu_func(layer.general.engine)
        else:
            yield layer.general.engine

        for arg in layer.arguments:
            yield from build_command_line_for_argument(arg)

    return list(_yield_args())


def combine_layers(layers: List[Layer]) -> Layer:
    pass  # TODO: apply in the loop
