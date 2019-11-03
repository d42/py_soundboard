import inspect
from typing import Dict

import sdl2.ext
from sdl2 import sdlmixer


def init_sdl():
    initialized = getattr(init_sdl, 'initialized', False)
    if initialized:
        return True

    sdl2.SDL_Init(0)
    sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_AUDIO)
    sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_JOYSTICK)
    sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b'1')

    result = sdlmixer.Mix_OpenAudio(
        sdlmixer.MIX_DEFAULT_FREQUENCY,
        sdlmixer.MIX_DEFAULT_FORMAT,
        2, 1024,
    ) != -1
    if result:
        setattr(init_sdl, 'initialized', True)
    return result


def read_func_attributes(func):
    spec = inspect.getfullargspec(func)
    args = {arg: None for arg in spec.args}
    if spec.defaults:
        defaults = {k: v for k, v in zip(reversed(spec.args), spec.defaults)}
    else:
        defaults = {}
    args.pop('self')  # TODO: do this better :3
    return args, defaults


# TODO: verify this
class Singleton(type):
    _instances: Dict[type, type] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
