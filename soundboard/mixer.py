import os
import wave
from threading import Thread
from time import sleep
from collections import deque, namedtuple


from sdl2 import sdlmixer

from soundboard.utils import init_sdl
from soundboard import constants

chunk_tuple = namedtuple('chunk_info', 'chunk duration')


class SDLMixer(Thread):
    def __init__(self, channel=0):
        self.sound_queue = deque()
        init_sdl()
        self.chunks = {}

    def init():
        init_sdl()

    def play(self, chunk):
        if sdlmixer.Mix_PlayChannel(-1, chunk, 0) == -1:
            raise Exception("Could not play chunk")

    def pump(self):
        if self.sound_queue:
            sound = self.sound_queue.pop()
            sound.play()

    def queue(self, **sounds):
        for s in sounds:
            self.sound_queue.append(s)

    def read(self, path):
        fs_path = os.path.join(constants.wav_directory, path)
        chunk = self.chunks.get(fs_path, self._load_chunk(fs_path))
        return RawSound(path, chunk, self)

    def _load_chunk(self, fs_path):
        chunk = sdlmixer.Mix_LoadWAV(fs_path.encode('utf-8'))
        wave_file = wave.open(fs_path)
        duration = wave_file.getnframes()/wave_file.getframerate()
        self.chunks[fs_path] = chunk_tuple(chunk, duration)
        return self.chunks[fs_path]


class NOPMixer(SDLMixer):

    def play(self, chunk):
        if sdlmixer.Mix_PlayChannel(-1, chunk, 0) == -1:
            raise Exception("Could not play chunk")
        sdlmixer.Mix_HaltChannel(-1)


class RawSound():
    def __init__(self, path, chunk, mixer):
        self.path = path
        self.duration = chunk.duration
        self.raw = chunk.chunk
        self.mixer = mixer

    def play(self):
        self.mixer.play(self.raw)
        sleep(self.duration - 0.25)
