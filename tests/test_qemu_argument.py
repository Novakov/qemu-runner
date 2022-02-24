import pytest

from qemu_runner.argument import *


@pytest.mark.parametrize(('arg', 'cmdline'), [
    (Argument(name='device'), ['-device']),
    (Argument(name='device', value='my-controller'), ['-device', 'my-controller']),

    (Argument(name='device', value='my-controller', attributes={
        'id': 'abc'
    }), ['-device', 'my-controller,id=abc']),
    (Argument(name='device', value='my-controller', attributes={
        'id': 'abc',
        'path': 'def',
    }), ['-device', 'my-controller,id=abc,path=def']),
    (Argument(name='device', value='my-controller', attributes={
        'path': 'def',
        'id': 'abc',
    }), ['-device', 'my-controller,id=abc,path=def']),
    (Argument(name='device', value='my-controller', attributes={
        'id': 'abc',
        'enable': None
    }), ['-device', 'my-controller,id=abc,enable']),

    (Argument(name='device', attributes={
        'id': 'abc'
    }), ['-device', 'id=abc']),
    (Argument(name='device', attributes={
        'id': 'abc',
        'path': 'def',
    }), ['-device', 'id=abc,path=def']),
    (Argument(name='device', attributes={
        'path': 'def',
        'id': 'abc',
    }), ['-device', 'id=abc,path=def']),

    (Argument(name='device', attributes={
        'enable': None,
        'id': 'abc',
    }), ['-device', 'id=abc,enable']),
])
def test_argument_cmdline(arg: Argument, cmdline: List[str]):
    actual = build_command_line_for_argument(arg)
    assert actual == cmdline


def test_argument_access_values():
    arg = Argument(name='device', value='nand-controller', attributes={
        'arg1': 12,
        'arg2': 'def'
    })

    assert arg.value == 'nand-controller'
    assert arg.attributes['arg1'] == 12
    assert arg.attributes['arg2'] == 'def'


def test_argument_access_id():
    arg = Argument(name='device', attributes={
        'arg1': 10,
        'id': 'my-id'
    })

    assert arg.id_value == 'my-id'


def test_argument_dont_set_empty_id():
    with pytest.raises(Exception):  # TODO: more specific exception
        Argument(name='device', attributes={'id': None})


def test_argument_access_id_no_id():
    arg = Argument(name='device', attributes={
        'arg1': 10,
    })

    assert arg.id_value is None


def test_argument_fail_create_with_non_str_id():
    with pytest.raises(Exception):  # TODO: more specific exception
        Argument(name='device', attributes={'id': 12})


def test_argument_update_value():
    arg = Argument(name='device', value='val1')
    updated = arg.replace_value('val2')

    assert updated.value == 'val2'


def test_argument_update_args():
    arg = Argument(name='device', attributes={
        'a': 1,
        'b': '2',
        'c': None
    })

    updated = arg.update_arguments({
        'a': 22,
        'b': 'xx',
        'z': 'yy'
    })

    assert updated.attributes == {
        'a': 22,
        'b': 'xx',
        'c': None,
        'z': 'yy'
    }


@pytest.mark.parametrize(('old', 'new'), [
    ('abc', 'abc'),
])
def test_argument_id_change_valid(old: ArgumentValue, new: ArgumentValue):
    arg = Argument(name='device', attributes={'id': old})
    updated = arg.update_arguments({'id': new})

    assert updated.id_value == new


@pytest.mark.parametrize(('old', 'new'), [
    ('abc', None),
    ('abc', 'def'),
])
def test_argument_id_change_invalid(old: ArgumentValue, new: ArgumentValue):
    arg = Argument(name='device', attributes={'id': old})
    with pytest.raises(Exception):  # TODO: more specific exception
        arg.update_arguments({'id': new})


def test_argument_remove_args():
    arg = Argument(name='device', attributes={
        'a': '1',
        'b': '2',
        'c': 3
    })

    updated = arg.remove_arguments(['a', 'b'])

    assert updated.attributes == {
        'c': 3
    }


def test_argument_cannot_remove_id():
    arg = Argument(name='device', attributes={'id': 'a'})
    with pytest.raises(Exception):  # TODO: more specific exception
        arg.remove_arguments(['id'])


@pytest.mark.parametrize(('a', 'b'), [
    (Argument('-device'), Argument('-device')),
    (Argument('-device', '', {'id': 'id1'}), Argument('-device', '', {'id': 'id1'})),
    (Argument('-device', '', {'id': 'id1', 'p': 'a'}), Argument('-device', '', {'id': 'id1'})),
    (Argument('-device', '', {'id': 'id1'}), Argument('-device', '', {'id': 'id1', 'p': 'a'})),
])
def test_argument_id_matches(a: Argument, b: Argument):
    assert a.id_matches(b)


@pytest.mark.parametrize(('a', 'b'), [
    (Argument('-device'), Argument('-chardev')),
    (Argument('-device', '', {'id': 'id1'}), Argument('-device')),
    (Argument('-device'), Argument('-device', '', {'id': 'id1'})),
    (Argument('-device', '', {'id': 'id1'}), Argument('-device', '', {'id': 'id2'})),
    (Argument('-device', '', {'id': 'id1'}), Argument('-chardev', '', {'id': 'id1'})),
])
def test_argument_id_not_matches(a: Argument, b: Argument):
    assert not a.id_matches(b)
