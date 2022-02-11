from typing import Tuple, Iterable

import pytest

from qemu_runner.argument import Argument

EQUAL_SETS = [
    [Argument('device')],
    [Argument('chardev')],
    [Argument('device', 'a')],
    [Argument('device', 'b')],
    [Argument('chardev', 'a')],
    [Argument('chardev', 'b')],
    [Argument('device', 'a', {'id': 'id1'})],
    [Argument('device', 'a', {'id': 'id2'})],
    [
        Argument('device', 'a', {'arg1': 1, 'arg2': 2}),
        Argument('device', 'a', {'arg2': 2, 'arg1': 1}),
    ],
    [
        Argument('device', 'a', {'arg1': 1, 'arg2': 2, 'arg3': 3}),
        Argument('device', 'a', {'arg2': 2, 'arg1': 1, 'arg3': 3}),
    ],
    [
        Argument('device', 'a', {'arg1': '1', 'arg2': '2', 'arg3': '3'}),
        Argument('device', 'a', {'arg2': '2', 'arg1': '1', 'arg3': '3'}),
    ]
]


def cases_equal() -> Iterable[Tuple[Argument, Argument]]:
    for equal_set in EQUAL_SETS:
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


def cases_not_equal() -> Iterable[Tuple[Argument, Argument]]:
    for a_idx in range(0, len(EQUAL_SETS)):
        for b_idx in range(a_idx, len(EQUAL_SETS)):
            if a_idx == b_idx:
                continue

            a_set = EQUAL_SETS[a_idx]
            b_set = EQUAL_SETS[b_idx]

            for a in a_set:
                for b in b_set:
                    yield a, b


@pytest.mark.parametrize(('a', 'b'), cases_equal())
def test_layer_equal(a: Argument, b: Argument):
    a = a.replace_value(a.value)
    b = b.replace_value(b.value)
    assert id(a) != id(b)
    assert a == b
    assert b == a


@pytest.mark.parametrize(('a', 'b'), cases_not_equal())
def test_layer_not_equal(a: Argument, b: Argument):
    a = a.replace_value(a.value)
    b = b.replace_value(b.value)
    assert id(a) != id(b)
    assert a != b
    assert b != a
