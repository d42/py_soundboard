from soundboard.mixer import SDLMixer
from soundboard.sounds import Sound
from sdl2 import sdlmixer


class NOPMixer(SDLMixer):

    def __init__(self, channel=0):
        super(NOPMixer, self).__init__(channel)
        self.played = []

    def play(self, chunk):
        self.played.append(chunk)
        if sdlmixer.Mix_PlayChannel(-1, chunk, 0) == -1:
            raise Exception("Could not play chunk")
        sdlmixer.Mix_HaltChannel(-1)


class TestSound(Sound):
    name = 'testtype'
    config_sounds_attribute = 'testinput'

    def setup(self, testinput, ebin=True):
        pass
