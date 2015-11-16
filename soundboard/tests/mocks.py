from soundboard.mixer import SDLMixer
from sdl2 import sdlmixer


class NOPMixer(SDLMixer):

    def __init__(self, channel=0):
        super(NOPMixer, self).__init__(channel)
        self.played = []

    def play(self, sound):
        self.played.append(sound.path)
        chunk = sound.raw
        if sdlmixer.Mix_PlayChannel(-1, chunk, 0) == -1:
            raise Exception("Could not play chunk")
        sdlmixer.Mix_HaltChannel(-1)
