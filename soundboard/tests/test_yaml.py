from soundboard.config import YAMLConfig


def test_yaml():
    test_file = 'soundboard/tests/test.yaml'
    y = YAMLConfig(test_file)
    y.name == 'test yaml'
    sound_1 = y.sounds[0]
    sound_1['name'] = 'whip'
    sound_1['position'] = 0
    sound_1['type'] = 'simple'
    sound_1['file'] = 'whip.wav'


def test_faulty_yaml():
    pass
