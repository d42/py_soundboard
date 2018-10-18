import os
import pytest

from ..schema import SoundSet
from ..config import settings, State
from .mocks import MockSound


@pytest.fixture
def sound_set():
    s = State()
    s.sounds.register(MockSound)
    ss = SoundSet()
    ss.context = dict(settings=settings, sounds=s.sounds)
    return ss


def test_sound_set(sound_set):
    data = {
        'name': 'ebin',
        'keys': {2, 3, 5},
        'modifiers': ['http'],
        'delay m': 0.25,
        'wav_directory': os.getcwd(),
        'delay c': 0,
        'sounds': [
            {
                'name': 'ebin',
                'type': 'testtype',
                'foo': ['ebin ebin'],
                'keys': {4},
                'testinput': ['herp', 'derp', 'durr']
            }
        ]
    }
    ebin, errors = sound_set.load(data)
    assert not errors
    assert ebin['name'] == 'ebin'
    assert len(ebin['keys']) == 3
    assert len(ebin['sounds']) == 1
    assert ebin['sounds'][0]['attributes'] == {
        'testinput': ['herp', 'derp', 'durr'],
        'ebin': True}


def test_sound_set_1(sound_set):

    data = {
        'name': 'ebin',
        'keys': {2, 3, 5},
        'modifiers': ['http'],
        'delay m': 0.25,
        'wav_directory': os.getcwd(),
        'delay c': 0,
        'sounds': [
            {
                'name': 'ebin',
                'type': 'testtype',
                'foo': ['ebin ebin'],
                'testinput': ['herp', 'derp', 'durr']
            }
        ]
    }

    ebin, errors = sound_set.load(data)
    assert not errors


def test_sound_set_2(sound_set):

    data = {
        'name': 'ebin',
        'keys': {2, 3, 5},
        'modifiers': ['http', 'floating'],
        'delay m': 0.25,
        'wav_directory': os.getcwd(),
        'delay c': 0,
        'sounds': [
            {
                'name': 'ebin',
                'type': 'testtype',
                'foo': ['ebin ebin'],
                'testinput': ['herp', 'derp', 'durr']
            }
        ]
    }
    ebin, errors = sound_set.load(data)
    assert not errors
