from typing import Protocol, Mapping

__all__ = [
    'VariableResolver',
    'resolve_no_variables',
    'append_resolver',
    'make_resolver_from_dict',
]


class VariableResolver(Protocol):
    def __call__(self, value: str) -> str:
        pass


def resolve_no_variables(value: str) -> str:
    return value


def append_resolver(base: VariableResolver, wrapper: VariableResolver) -> VariableResolver:
    def resolver(value: str) -> str:
        return wrapper(base(value))

    return resolver


def make_resolver_from_dict(variables: Mapping[str, str]) -> VariableResolver:
    substitutions = {f'${{{k}}}': v for k, v in variables.items()}

    def resolver(value: str) -> str:
        result = value
        for k, v in substitutions.items():
            result = result.replace(k, v)

        return result

    return resolver
