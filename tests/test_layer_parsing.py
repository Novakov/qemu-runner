from configparser import ConfigParser

import pytest

from qemu_runner.argument import Argument
from qemu_runner.layer import Layer, GeneralSettings, parse_layer


@pytest.mark.parametrize(('text', 'expected'), [
    (
            """
            [general]
            engine = my-engine
            """,
            Layer(general=GeneralSettings(engine='my-engine'))
    ),
    (
            '',
            Layer()
    ),
    (
            """
            [device]
            """,
            Layer(arguments=[Argument('device')])
    ),
    (
            """
            [device]
            @=def
            """,
            Layer(arguments=[Argument('device', 'def')])
    ),
    (
            """
            [device]
            arg1=1
            arg2=2
            """,
            Layer(arguments=[Argument('device', arguments={'arg1': '1', 'arg2': '2'})])
    ),
    (
            """
            [device:d1]
            arg1=1
            arg2=2
            """,
            Layer(arguments=[Argument('device', arguments={'id': 'd1', 'arg1': '1', 'arg2': '2'})])
    ),
    (
            """
            [device:d1]
            arg1=1
            arg2=2
    
            [device:d2]
            arg3=3
            arg4=4
            """,
            Layer(arguments=[
                Argument('device', arguments={'id': 'd1', 'arg1': '1', 'arg2': '2'}),
                Argument('device', arguments={'id': 'd2', 'arg3': '3', 'arg4': '4'})
            ])
    ),
    (
            """
            [device]
            arg1=1
            arg2=2
    
            [device:d2]
            arg3=3
            arg4=4
            """,
            Layer(arguments=[
                Argument('device', arguments={'arg1': '1', 'arg2': '2'}),
                Argument('device', arguments={'id': 'd2', 'arg3': '3', 'arg4': '4'})
            ])
    )
])
def test_load_layer_from_file(text: str, expected: Layer):
    parser = ConfigParser()
    parser.read_string(text)
    layer = parse_layer(parser)
    assert layer == expected