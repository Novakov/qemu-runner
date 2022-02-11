from typing import Callable, Iterable, Tuple

import pytest

from qemu_runner.argument import Argument
from qemu_runner.layer import Layer, GeneralSettings

ARG1 = Argument('device')
ARG2 = Argument('chardev')
ARG3 = Argument('chardev')

EQUAL_LAYERS = [
    [lambda: Layer()],
    [lambda: Layer(general=GeneralSettings(engine='my-engine'))],
    [lambda: Layer(general=GeneralSettings(engine='my-engine2'))],
    [lambda: Layer(arguments=[Argument('device')])],
    [lambda: Layer(general=GeneralSettings(engine='my-engine'), arguments=[ARG1])],
    [lambda: Layer(general=GeneralSettings(engine='my-engine'), arguments=[ARG2])],
    [
        lambda: Layer(general=GeneralSettings(engine='my-engine'), arguments=[ARG1, ARG2]),
        lambda: Layer(general=GeneralSettings(engine='my-engine'), arguments=[ARG2, ARG1]),
    ],
    [
        lambda: Layer(general=GeneralSettings(engine='my-engine'), arguments=[ARG1, ARG2, ARG3]),
        lambda: Layer(general=GeneralSettings(engine='my-engine'), arguments=[ARG1, ARG3, ARG2]),
        lambda: Layer(general=GeneralSettings(engine='my-engine'), arguments=[ARG3, ARG1, ARG2]),
    ],
]

LayerFactory = Callable[[], Layer]


def cases_equal() -> Iterable[Tuple[LayerFactory, LayerFactory]]:
    for equal_set in EQUAL_LAYERS:
        if len(equal_set) == 1:
            yield equal_set[0], equal_set[0]
        elif len(equal_set) == 2:
            yield equal_set[0], equal_set[1]
        else:
            for a_idx in range(0, len(equal_set)):
                for b_idx in range(a_idx, len(equal_set)):
                    if a_idx == b_idx:
                        continue

                    yield equal_set[a_idx], equal_set[b_idx]


def cases_not_equal() -> Iterable[Tuple[LayerFactory, LayerFactory]]:
    for a_idx in range(0, len(EQUAL_LAYERS)):
        for b_idx in range(a_idx, len(EQUAL_LAYERS)):
            if a_idx == b_idx:
                continue

            a_set = EQUAL_LAYERS[a_idx]
            b_set = EQUAL_LAYERS[b_idx]

            for a in a_set:
                for b in b_set:
                    yield a, b


@pytest.mark.parametrize(('a', 'b'), cases_equal())
def test_layer_equal(a: LayerFactory, b: LayerFactory):
    layer_a = a()
    layer_b = b()

    assert id(layer_a) != id(layer_b)
    assert layer_a == layer_b
    assert layer_b == layer_a


@pytest.mark.parametrize(('a', 'b'), cases_not_equal())
def test_layer_not_equal(a: LayerFactory, b: LayerFactory):
    layer_a = a()
    layer_b = b()

    assert id(layer_a) != id(layer_b)
    assert layer_a != layer_b
    assert layer_b != layer_a
