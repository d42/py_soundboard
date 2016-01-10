from soundboard.sounds import SoundSet, SoundInterface

test_config = {
    'name': 'default',
    'keys': frozenset([2, 3]),
    'wav_directory': 'sounds/',
    'delay constant': 0,
    'delay multiplier': 0,
    'sounds': [
        {
            'name': 'whip',
            'keys': frozenset([0]),
            'type': 'simple',
            'attributes': {'path': 'test/test.wav'},
        },
        {
            'name': 'random whip',
            'keys': frozenset([1]),
            'type': 'random',
            'attributes': {'paths': ['test/test.wav', 'test/test2.wav']},
        },
        {
            'name': 'vox test',
            'keys': frozenset([2]),
            'type': 'vox',
            'attributes': {'sentence': 'test test'},
        },
    ]


}


def test_1():
    s = SoundSet(test_config)
    assert len(s.sounds) == 3
    assert all(isinstance(s, SoundInterface) for s in s.sounds.values())
