from soundboard.config import YAMLConfig


def test_yaml():
    test_file = "soundboard/tests/testboard/yaml/test.yaml"
    y = YAMLConfig(test_file)
    assert y["name"] == "Test Board"
    sound_1 = y["sounds"][0]
    assert sound_1["name"] == "whip"
    assert sound_1["keys"] == frozenset([0])
    assert sound_1["type"] == "simple"
    assert sound_1["attributes"]["path"] == "test.wav"
