from sdl2 import sdlmixer

from soundboard.mixer import SDLMixer
from soundboard.sounds import Sound


class NOPMixer(SDLMixer):
    def __init__(self):
        super().__init__()
        self.played = []

    def play(self, chunk):
        self.played.append(chunk)
        if sdlmixer.Mix_PlayChannel(-1, chunk, 0) == -1:
            raise Exception("Could not play chunk")
        sdlmixer.Mix_HaltChannel(-1)


class MockSound(Sound):
    name = "testtype"
    config_sounds_attribute = "testinput"

    def setup(self, testinput, ebin=True):
        pass
