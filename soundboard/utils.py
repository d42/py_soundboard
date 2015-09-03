import sdl2
import sdl2.ext
from sdl2 import sdlmixer


def init_sdl():
    initialized = getattr(init_sdl, 'initialized', False)
    if initialized:
        return True

    sdl2.SDL_Init(0)
    sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_AUDIO)
    sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_JOYSTICK)

    result = sdlmixer.Mix_OpenAudio(sdlmixer.MIX_DEFAULT_FREQUENCY,
                                    sdlmixer.MIX_DEFAULT_FORMAT,
                                    2, 1024) != -1
    if result:
        setattr(init_sdl, 'initialized', True)
    return result
