import pytest

from qemu_runner.layer import *


def test_empty_layer_def():
    layer = Layer()

    assert len(layer.arguments) == 0
    assert layer.general.engine == ''


def test_create_layer():
    layer = Layer(
        general=GeneralSettings(
            engine='my-engine'
        ),
        arguments=[
            Argument('device', 'nand-controller', {'id': 'id1', 'path': 'path1'}),
            Argument('device', 'i2c-controller', {'id': 'id2', 'path': 'path1'}),
        ]
    )

    assert layer.general.engine == 'my-engine'
    assert len(layer.arguments) == 2
    assert layer.arguments[0] == Argument('device', 'nand-controller', {'id': 'id1', 'path': 'path1'})
    assert layer.arguments[1] == Argument('device', 'i2c-controller', {'id': 'id2', 'path': 'path1'})


MY_ENGINE = GeneralSettings(engine='my-engine')
MY_ENGINE2 = GeneralSettings(engine='my-engine2')

LAYER_APPLY_CASES = [
    (Layer(), Layer(), Layer()),
    (Layer(MY_ENGINE), Layer(), Layer(MY_ENGINE)),
    (Layer(), Layer(MY_ENGINE), Layer(MY_ENGINE)),
    (Layer(MY_ENGINE), Layer(MY_ENGINE2), Layer(MY_ENGINE2)),
    (
        Layer(GeneralSettings(engine='e1', kernel='k1', kernel_cmdline='c1', halted=False, gdb=False, gdb_dev='gdb1')),
        Layer(GeneralSettings(engine='e2', kernel='k2', kernel_cmdline='c2', halted=True, gdb=True, gdb_dev='gdb2')),
        Layer(GeneralSettings(engine='e2', kernel='k2', kernel_cmdline='c1 c2', halted=True, gdb=True, gdb_dev='gdb2')),
    ),
    (
        Layer(GeneralSettings(memory='12')),
        Layer(GeneralSettings()),
        Layer(GeneralSettings(memory='12')),
    ),
    (
        Layer(GeneralSettings(memory='12')),
        Layer(GeneralSettings(memory='24')),
        Layer(GeneralSettings(memory='24')),
    ),
    (
        Layer(GeneralSettings()),
        Layer(GeneralSettings(memory='24')),
        Layer(GeneralSettings(memory='24')),
    ),
    (
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p': 'a'})]),
        Layer(MY_ENGINE, [Argument('chardev', 'c1', {'id': 'id2', 'b': 'a'})]),
        Layer(MY_ENGINE, [
            Argument('device', 'd1', {'id': 'id1', 'p': 'a'}),
            Argument('chardev', 'c1', {'id': 'id2', 'b': 'a'})
        ]),
    ),
    (
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p': 'a'})]),
        Layer(MY_ENGINE, []),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p': 'a'})]),
    ),
    (
        Layer(MY_ENGINE, []),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p': 'a'})]),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p': 'a'})]),
    ),
    (
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p1': 'v1'})]),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p2': 'v2'})]),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p1': 'v1', 'p2': 'v2'})]),
    ),
    (
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p1': 'v1'})]),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p2': 'v2'}), Argument('-gdb')]),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p1': 'v1', 'p2': 'v2'}), Argument('-gdb')]),
    ),
    (
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p1': 'v1'})]),
        Layer(MY_ENGINE, [Argument('device', 'd2', {'id': 'id1', 'p2': 'v2'}), Argument('-gdb')]),
        Layer(MY_ENGINE, [Argument('device', 'd2', {'id': 'id1', 'p1': 'v1', 'p2': 'v2'}), Argument('-gdb')]),
    ),
    (
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p1': 'v1'})]),
        Layer(MY_ENGINE, [Argument('device', None, {'id': 'id1', 'p2': 'v2'}), Argument('-gdb')]),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p1': 'v1', 'p2': 'v2'}), Argument('-gdb')]),
    ),
    (
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id1', 'p1': 'v1'})]),
        Layer(MY_ENGINE, [Argument('device', 'd1', {'id': 'id2', 'p2': 'v2'}), Argument('-gdb')]),
        Layer(MY_ENGINE, [
            Argument('device', 'd1', {'id': 'id1', 'p1': 'v1'}),
            Argument('device', 'd1', {'id': 'id2', 'p2': 'v2'}),
            Argument('-gdb')
        ]),
    ),
]


@pytest.mark.parametrize(('base_layer', 'addition', 'expected'), LAYER_APPLY_CASES)
def test_apply_layer(base_layer: Layer, addition: Layer, expected: Layer):
    actual = base_layer.apply(addition)
    assert actual == expected
