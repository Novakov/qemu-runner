from configparser import ConfigParser
from typing import List

from .argument import Argument


# TODO: named tuple/dataclass
class GeneralSettings:
    engine: str


class Layer:
    general: GeneralSettings
    arguments: List[Argument]

    def apply(self, addition: 'Layer') -> 'Layer':
        pass  # TODO

    @staticmethod
    @property
    def empty() -> 'Layer':
        pass  # TODO


def parse_layer(config_parser: ConfigParser) -> Layer:
    pass  # TODO


def build_command_line(layer: Layer) -> List[str]:
    pass  # TODO


def combine_layers(layers: List[Layer]) -> Layer:
    pass  # TODO: apply in the loop
