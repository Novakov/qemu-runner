from configparser import ConfigParser

import pytest

from qemu_runner.argument import Argument
from qemu_runner.layer import Layer, GeneralSettings, parse_layer, Mode


@pytest.mark.parametrize(('text', 'expected'), [
    (
            """
            [general]
            engine = my-engine
            """,
            Layer(general=GeneralSettings(engine='my-engine'))
    ),
    (
            """
            [general]
            memory = 128M
            """,
            Layer(general=GeneralSettings(memory='128M'))
    ),
    (
            """
            [general]
            engine = my-engine
            kernel = my-kernel.elf
            cmdline = a b c
            """,
            Layer(general=GeneralSettings(engine='my-engine', kernel='my-kernel.elf', kernel_cmdline='a b c'))
    ),
    (
            """
            [general]
            engine = my-engine
            kernel = my-kernel.elf
            mode = user
            """,
            Layer(general=GeneralSettings(engine='my-engine', kernel='my-kernel.elf', mode=Mode.User))
    ),
    (
            """
            [general]
            engine = my-engine
            gdb = yes
            """,
            Layer(general=GeneralSettings(engine='my-engine', gdb=True))
    ),
    (
            """
            [general]
            engine = my-engine
            gdb = no
            """,
            Layer(general=GeneralSettings(engine='my-engine', gdb=False))
    ),
    (
            """
            [general]
            engine = my-engine
            gdb_dev = tcp::5555
            """,
            Layer(general=GeneralSettings(engine='my-engine', gdb_dev='tcp::5555'))
    ),
    (
            """
            [general]
            engine = my-engine
            halted = yes
            """,
            Layer(general=GeneralSettings(engine='my-engine', halted=True))
    ),
    (
            """
            [general]
            engine = my-engine
            halted = no
            """,
            Layer(general=GeneralSettings(engine='my-engine', halted=False))
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
            Layer(arguments=[Argument('device', attributes={'arg1': '1', 'arg2': '2'})])
    ),
    (
            """
            [device:d1]
            arg1=1
            arg2=2
            """,
            Layer(arguments=[Argument('device', attributes={'id': 'd1', 'arg1': '1', 'arg2': '2'})])
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
                Argument('device', attributes={'id': 'd1', 'arg1': '1', 'arg2': '2'}),
                Argument('device', attributes={'id': 'd2', 'arg3': '3', 'arg4': '4'})
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
                Argument('device', attributes={'arg1': '1', 'arg2': '2'}),
                Argument('device', attributes={'id': 'd2', 'arg3': '3', 'arg4': '4'})
            ])
    )
])
def test_load_layer_from_file(text: str, expected: Layer):
    parser = ConfigParser()
    parser.read_string(text)
    layer = parse_layer(parser)
    assert layer == expected
