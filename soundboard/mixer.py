import wave
from collections import namedtuple
from time import sleep

from sdl2 import sdlmixer

from .config import settings
from .utils import Singleton
from soundboard.utils import init_sdl

chunk_tuple = namedtuple("chunk_info", "chunk duration")


class SDLMixer(metaclass=Singleton):
    def __init__(self):
        super().__init__()
        init_sdl()
        self.chunks = {}

    @staticmethod
    def play(chunk):
        if sdlmixer.Mix_PlayChannel(-1, chunk, 0) == -1:
            raise Exception("Could not play chunk")

    def read(self, path):
        chunk = self.chunks.get(path, self._load_chunk(path))
        return RawSound(path, chunk, self)

    def _load_chunk(self, fs_path):
        chunk = sdlmixer.Mix_LoadWAV(fs_path.encode("utf-8"))
        wave_file = wave.open(fs_path)
        duration = wave_file.getnframes() / wave_file.getframerate()
        self.chunks[fs_path] = chunk_tuple(chunk, duration)
        return self.chunks[fs_path]


class NOPMixer(SDLMixer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.played = []

    def play(self, sound):
        self.played.append(sound.path)
        chunk = sound.raw
        if sdlmixer.Mix_PlayChannel(-1, chunk, 0) == -1:
            raise Exception("Could not play chunk")
        sdlmixer.Mix_HaltChannel(-1)


class RawSound:
    def __init__(self, path, chunk, mixer):
        self.path = path
        self.duration = chunk.duration
        self.raw = chunk.chunk
        self.mixer = mixer

    def play(self, duration_const=0, is_async=False):
        self.mixer.play(self.raw)
        if is_async:
            return
        sleep((self.duration + duration_const) - settings.sound_sleep_offset)
