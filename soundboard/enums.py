from enum import Enum

import sdl2


class EventTypes(Enum):
    release = 0
    push = 1
    hold = 2

    new_push = 1000

    @classmethod
    def from_sdl(cls, sdl_event):
        sdl_event_types = {
            sdl2.SDL_JOYBUTTONDOWN: cls.push,
            sdl2.SDL_JOYBUTTONUP: cls.release
        }
        return sdl_event_types[sdl_event]


class ModifierTypes(Enum):
    floating = 'floating'
    http = 'http'
