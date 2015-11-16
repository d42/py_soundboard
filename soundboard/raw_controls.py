import logging

import sdl2
import sdl2.ext
import evdev
import evdev.ecodes

from .exceptions import ControllerException
from .utils import init_sdl
from .types import event_tuple
from .enums import EventTypes

logger = logging.getLogger('controls.raw')


class BaseRawJoystick(object):

    def __init__(self, mapping=None, offset=0):
        self.mapping = mapping if mapping else dict()
        self.scancode_offset = offset
        self.events = list()
        self.pushed = set()

    @property
    def isempty(self):
        return len(self.events) == 0

    def pop_events(self):
        events = self.events
        self.events = []
        return events

    def process(self, events, preprocess_func):
        """ :type events: list(EventTypes)"""
        """ :type preprocess: func -> event_tuple"""
        if preprocess_func:
            events = [preprocess_func(e) for e in events]

        events = [self.translate(e) for e in events]

        self.events.extend(events)

    def translate(self, event):
        """:type event: event_tuple"""
        def shift(button): return button - self.scancode_offset

        def remap(button): return self.mapping.get(button, button)
        button, type = event
        new_button = remap(shift(button))
        return event_tuple(new_button, type)


class RawSDLJoystick(BaseRawJoystick):
    JOYSTICK_EVENTS = (sdl2.SDL_JOYBUTTONUP, sdl2.SDL_JOYBUTTONDOWN)

    def __init__(self, joystick_id, mapping=None, offset=0):
        super(RawSDLJoystick, self).__init__(mapping, offset)
        init_sdl()
        self.joystick = self.open_joystick(joystick_id)

    @staticmethod
    def open_joystick(joystick_id):
        joystick = sdl2.SDL_JoystickOpen(joystick_id)
        if not joystick:
            text = "Joystick %d could not be initialized" % joystick_id
            raise ControllerException(text)
        return joystick

    def update(self):

        def to_tuple(event):
            button = event.button.jbutton
            type = EventTypes.from_sdl(event.type)
            return event_tuple(button, type)

        events = []
        all_events = sdl2.ext.get_events()
        events = [e for e in all_events if e.type in self.JOYSTICK_EVENTS]
        self.process(events, preprocess_func=to_tuple)


class RawEVDEVJoystick(BaseRawJoystick):
    JOYSTICK_EVENTS = [evdev.ecodes.EV_KEY]

    def __init__(self, device_path, mapping=None, offset=0):
        super(RawEVDEVJoystick, self).__init__(mapping, offset)
        self.joystick = evdev.InputDevice(device_path)
        self.set_caps()

    def set_caps(self):
        if self.joystick.repeat == (0, 0):
            self.autorepeat = False

    def _read(self):
        try:
            ebin = list(self.joystick.read())
        except:
            return []
        return ebin

    def update(self):
        def to_tuple(event):
            type = EventTypes(event.value)
            button = event.code
            return event_tuple(button, type)

        events = [e for e in self._read() if e.type in self.JOYSTICK_EVENTS]
        self.process(events, to_tuple)

handlers = {
    'sdl': RawSDLJoystick,
    'evdev': RawEVDEVJoystick
}
