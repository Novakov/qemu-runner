from typing import List
from unittest.mock import Mock

import pytest

from qemu_runner.argument import Argument
from qemu_runner.layer import Layer, build_command_line, GeneralSettings

MY_ENGINE = GeneralSettings(engine='my-engine')


@pytest.mark.parametrize(('layer', 'cmdline'), [
    (
            Layer(MY_ENGINE),
            ['my-engine']
    ),
    (
            Layer(GeneralSettings(engine='my-engine', halted=True)),
            ['my-engine', '-S']
    ),
    (
            Layer(GeneralSettings(engine='my-engine', gdb=True)),
            ['my-engine', '-s']
    ),
    (
            Layer(GeneralSettings(engine='my-engine', gdb=True, gdb_dev='tcp::5555')),
            ['my-engine', '-gdb', 'tcp::5555']
    ),
    (
            Layer(GeneralSettings(engine='my-engine', gdb=False, gdb_dev='tcp::5555')),
            ['my-engine']
    ),
    (
            Layer(MY_ENGINE, [Argument('device', 'val1', {'id': 'id1', 'path': 'path1'})]),
            ['my-engine', '-device', 'val1,id=id1,path=path1']
    ),
    (
            Layer(GeneralSettings(engine='my-engine', kernel='abc.elf')),
            ['my-engine', '-kernel', 'abc.elf']
    ),
    (
            Layer(GeneralSettings(engine='my-engine', kernel='abc.elf', kernel_cmdline='a b c')),
            ['my-engine', '-kernel', 'abc.elf', '-append', 'a b c']
    ),
    (
            Layer(
                GeneralSettings(engine='my-engine', halted=True, gdb=True, kernel='abc.elf', kernel_cmdline='a b c'),
                [Argument('device', 'val1', {'id': 'id1', 'path': 'path1'})]
            ),
            ['my-engine', '-device', 'val1,id=id1,path=path1', '-S', '-s', '-kernel', 'abc.elf', '-append', 'a b c']
    ),
])
def test_build_command_line(layer: Layer, cmdline: List[str]):
    actual = build_command_line(layer)
    assert actual == cmdline


def test_fail_when_no_engine():
    layer = Layer(general=GeneralSettings(engine=''))

    with pytest.raises(Exception):  # TODO: more specific exception
        build_command_line(layer)


def test_resolve_engine_path():
    find_qemu_func = Mock()
    find_qemu_func.return_value = 'abc'

    cmdline = build_command_line(Layer(general=GeneralSettings(engine='my-engine')), find_qemu_func=find_qemu_func)

    assert cmdline == ['abc']
    find_qemu_func.assert_called_once_with('my-engine')


