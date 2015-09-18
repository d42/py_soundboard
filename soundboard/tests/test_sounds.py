import pytest

from soundboard import sounds
from soundboard.mixer import NOPMixer


@pytest.fixture
def factory():
    return sounds.SoundFactory(NOPMixer)


def test_sounds(factory):
    simple = factory.simple("test/test.wav")
    simple.play()

    vox = factory.vox("test")
    vox.play()

    list = factory.list(["test/test.wav", "test/test.wav"])
    list.play()

    random = factory.random(["test/test.wav", "test/test.wav"])
    random.play()
