import os
import pytest  # noqa
from ..schema import SoundSet
from ..config import settings, state


@state.sounds.register
class TestSound:
    simple_name = 'testtype'
    config_sounds_attribute = 'testinput'


def test_sound_set():
    data = {
        'name': 'ebin',
        'keys': {2, 3, 5},
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
    ss = SoundSet().bind(settings=settings, sounds=state.sounds)
    ebin = ss.deserialize(data)
    assert ebin['name'] == 'ebin'
    assert len(ebin['keys']) == 3
    assert len(ebin['sounds']) == 1
    assert ebin['sounds'][0]['input'] == ['herp', 'derp', 'durr']
