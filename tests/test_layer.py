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



# TODO: layer apply empty == layer
# TODO: commandline for layer
# TODO: commandline for layer, no engine
# TODO: commandline for layer, some args
# TODO: apply (blob)
