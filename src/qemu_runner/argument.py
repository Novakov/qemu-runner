from dataclasses import dataclass, field, replace
from typing import Union, Mapping, Optional

ArgumentValue = Union[int, str, None]


@dataclass(frozen=True)
class Argument:
    name: str
    value: ArgumentValue = None
    arguments: Mapping[str, ArgumentValue] = field(default_factory=dict)

    def __post_init__(self):
        if 'id' in self.arguments:
            if self.id_value is None:
                raise Exception("ID must not be None")  # TODO: more specific exception

            if not isinstance(self.id_value, str):
                raise Exception('ID must be string')  # TODO: more specific exception

    @property
    def id_value(self) -> Optional[str]:
        return self.arguments.get('id', None)

    def replace_value(self, new_value: ArgumentValue) -> 'Argument':
        return replace(self, value=new_value)

    def update_arguments(self, new_values: Mapping[str, ArgumentValue]) -> 'Argument':
        if self.id_value is not None and self.id_value != new_values.get('id', None):
            raise Exception('Cannot change value of ID')  # TODO: more specific exception

        updated_args = dict(self.arguments)
        updated_args.update(new_values)
        return replace(self, arguments=updated_args)

    def remove_arguments(self, names: list[str]):
        if 'id' in names:
            raise Exception('Cannot remove assigned id')
        updated = dict(self.arguments)
        for n in names:
            del updated[n]

        return replace(self, arguments=updated)


def build_command_line_for_argument(argument: Argument) -> list[str]:
    result = [f'-{argument.name}']

    arg_value = []
    if argument.value:
        arg_value.append(argument.value)

    if argument.id_value is not None:
        arg_value.append(f'id={argument.id_value}')

    for k, v in argument.arguments.items():
        if k == 'id':
            continue

        if v is None:
            arg_value.append(k)
        else:
            arg_value.append(f'{k}={v}')

    if arg_value:
        result.append(','.join(arg_value))

    return result