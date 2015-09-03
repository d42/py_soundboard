from soundboard.sounds import SimpleSound, VoxSound
from soundboard.mixer import NOPMixer
from soundboard.utils import init_sdl


def test_raw():
    mixer = NOPMixer()
    initialized = init_sdl()
    assert initialized is True
    s = SimpleSound("default/whip.wav", mixer=mixer)
    # s = RawVox("is")
