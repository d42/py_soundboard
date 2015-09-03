from soundboard.sounds import SoundSet, SoundInterface


def test_1():
    s = SoundSet('test')
    assert len(s.sounds) == 2
    assert all(isinstance(s, SoundInterface) for s in s.sounds.values())
